import socket
import threading
import random

class Server:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.parties = {}
        self.next_game_id = 1
        self.lock = threading.Lock()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Le serveur est démarré et attend des connexions...")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connexion acceptée de {client_address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        print("Gestion d'un nouveau client...")
        partie = self.choisir_partie(client_socket)
        if partie is None:
            print("Aucune partie sélectionnée. Fermeture de la connexion.")
            client_socket.close()
            return

        client_socket.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
        nom_client = client_socket.recv(1024).decode().strip()

        with self.lock:
            joueur_id = len(partie.joueurs) + 1
            partie.ajouter_joueur(nom_client, client_socket, joueur_id)
            print(f"{nom_client} (ID: {joueur_id}) a rejoint la partie {partie.id_partie}")

            if not partie.jeu_commence:
                partie.commencer_partie()
                print(f"Partie {partie.id_partie} commence avec {len(partie.joueurs)} joueur(s).")

        partie.gerer_client(client_socket, nom_client)

    def choisir_partie(self, client_socket):
        while True:
            print("Envoi de la liste des parties disponibles...")
            if self.parties:
                client_socket.send("Parties disponibles :\n".encode())
                for id_partie, partie in self.parties.items():
                    status = "commencée" if partie.jeu_commence else "non commencée"
                    client_socket.send(f"Partie {id_partie} ({status}) \n".encode())
            else:
                client_socket.send("Aucune partie disponible. Vous pouvez créer une nouvelle partie.\n".encode())

            client_socket.send("Tapez l'ID de la partie pour la rejoindre ou 'nouvelle' pour en créer une : ".encode())
            choix = client_socket.recv(1024).decode().strip()

            if choix.lower() == "nouvelle":
                with self.lock:
                    id_partie = self.next_game_id
                    partie = Partie(id_partie)
                    self.parties[id_partie] = partie
                    self.next_game_id += 1
                print(f"Nouvelle partie créée avec l'ID {id_partie}")
                client_socket.send(f"Nouvelle partie {id_partie} créée.\n".encode())
                return partie

            try:
                id_partie = int(choix)
                if id_partie in self.parties:
                    partie = self.parties[id_partie]
                    if partie.jeu_commence:
                        print(f"La partie {id_partie} est déjà commencée.")
                        client_socket.send("La partie a déjà commencé. Veuillez choisir une autre partie ou créer une nouvelle.\n".encode())
                    else:
                        print(f"Le client rejoint la partie {id_partie}")
                        client_socket.send(f"Vous avez rejoint la partie {id_partie}.\n".encode())
                        return partie
                else:
                    print(f"ID de partie invalide : {id_partie}")
                    client_socket.send("Partie invalide. Veuillez réessayer.\n".encode())
            except ValueError:
                print("Entrée non valide pour la sélection de la partie.")
                client_socket.send("Entrée non valide. Veuillez réessayer.\n".encode())


class Partie:
    def __init__(self, id_partie):
        self.id_partie = id_partie
        self.joueurs = {}  # {nom: socket}
        self.tours_termines = 0
        self.jeu_commence = False
        self.scores = {}
        self.elimines = []  # Liste des joueurs éliminés
        self.lock = threading.Lock()  # Pour gérer l'accès concurrent

    def ajouter_joueur(self, nom, client_socket, joueur_id):
        """Ajoute un joueur à la partie."""
        with self.lock:
            self.joueurs[nom] = client_socket
        print(f"Joueur {nom} ajouté à la partie {self.id_partie} (ID joueur : {joueur_id})")

    def commencer_partie(self):
        """Marque le début de la partie."""
        self.jeu_commence = True
        print(f"Partie {self.id_partie} démarre maintenant avec {len(self.joueurs)} joueur(s).")

    def eliminer_joueur(self, nom_client):
        """Élimine un joueur et met à jour les joueurs restants."""
        with self.lock:
            if nom_client in self.joueurs:
                self.elimines.append(nom_client)
                self.joueurs.pop(nom_client)
                print(f"{nom_client} a quitté la partie {self.id_partie}. Joueur éliminé.")
                self.notifier_retrait_joueur(nom_client)

    def notifier_retrait_joueur(self, nom_client):
        """Informe les joueurs restants qu'un joueur a quitté."""
        for joueur, socket in self.joueurs.items():
            try:
                socket.send(f"{nom_client} a quitté la partie.\n".encode())
            except BrokenPipeError:
                print(f"Erreur lors de la notification au joueur {joueur}.")

    def gerer_client(self, client_socket, nom_client):
        """Gère le déroulement des tours pour un joueur."""
        total_score = 0
        print(f"Début de la gestion des tours pour le joueur {nom_client}.")

        for tour in range(6):
            if nom_client in self.elimines:
                print(f"{nom_client} est éliminé. Ignorer ses tours.")
                return

            try:
                points = self.tour_de_jeu(client_socket, nom_client)
                total_score += points
                client_socket.send(f"Tour {tour + 1} terminé. Score actuel : {total_score}.\n".encode())
            except (ConnectionResetError, BrokenPipeError):
                print(f"{nom_client} a quitté la partie pendant le tour.")
                self.eliminer_joueur(nom_client)
                return

        if nom_client not in self.elimines:
            print(f"Le joueur {nom_client} a terminé avec un score total de {total_score}.")
            with self.lock:
                self.scores[nom_client] = total_score
                self.tours_termines += 1

        with self.lock:
            if len(self.joueurs) == 1:  # S'il ne reste qu'un seul joueur
                dernier_joueur = list(self.joueurs.keys())[0]
                self.declarer_gagnant_unique(dernier_joueur)
            elif self.tours_termines == len(self.joueurs):
                self.terminer_partie()

    def tour_de_jeu(self, client_socket, nom):
        """Gère un tour de jeu pour un joueur."""
        des = self.lancer_des()
        client_socket.send(f"{nom}, Premier lancer : {des}\n".encode())

        lancers = 1
        valeur_gardee = None

        while lancers < 3:
            client_socket.send(f"{nom}, Entrez la valeur des dés à garder, 'fin' pour ne pas relancer, ou 'quitter' pour quitter : ".encode())
            choix = client_socket.recv(1024).decode().strip()

            if choix.lower() == "fin":
                print(f"{nom} a choisi de terminer la partie via 'fin'.")
                self.eliminer_joueur(nom)
                raise ConnectionResetError
            elif choix.lower() == "quitter":
                print(f"{nom} a choisi de quitter la partie.")
                self.eliminer_joueur(nom)
                raise ConnectionResetError

            try:
                valeur_gardee = int(choix)
                if valeur_gardee in des:
                    des = self.relancer_des(des, valeur_gardee)
                    lancers += 1
                    client_socket.send(f"{nom}, Lancer suivant : {des}\n".encode())
                else:
                    client_socket.send(f"Entrée non valide, la valeur {valeur_gardee} ne fait pas partie des dés {des}.\n".encode())
            except ValueError:
                client_socket.send(f"Entrée non valide. Veuillez réessayer.\n".encode())

        points = des.count(valeur_gardee) * valeur_gardee if valeur_gardee else sum(des)
        return points

    def terminer_partie(self):
        """Clôture la partie et déclare le gagnant."""
        if not self.scores:
            print("Tous les joueurs ont quitté la partie. Aucun gagnant.")
            for joueur, socket in self.joueurs.items():
                socket.send("Tous les autres joueurs ont quitté. Aucun gagnant.\n".encode())
                socket.close()
            return

        gagnant = max(self.scores, key=self.scores.get)
        print(f"Fin de la partie {self.id_partie}. Le gagnant est {gagnant} avec un score de {self.scores[gagnant]} points.")
        for joueur, socket in self.joueurs.items():
            if joueur == gagnant:
                socket.send(f"Félicitations {joueur}, vous avez gagné avec un score de {self.scores[joueur]} points !\n".encode())
            else:
                socket.send(f"Désolé {joueur}, vous avez perdu. Le gagnant est {gagnant}.\n".encode())
            socket.close()

    def declarer_gagnant_unique(self, dernier_joueur):
        """Déclare le dernier joueur comme gagnant par défaut."""
        client_socket = self.joueurs[dernier_joueur]
        client_socket.send(f"Félicitations {dernier_joueur}, vous êtes le gagnant car tous les autres joueurs ont quitté !\n".encode())
        client_socket.close()

    @staticmethod
    def lancer_des():
        """Lance 5 dés."""
        return [random.randint(1, 6) for _ in range(5)]

    @staticmethod
    def relancer_des(des, valeur_gardee):
        """Relance les dés sauf ceux correspondant à la valeur gardée."""
        return [random.randint(1, 6) if d != valeur_gardee else d for d in des]




if __name__ == "__main__":
    server = Server()
    server.start()
