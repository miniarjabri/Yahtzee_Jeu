import socket
import threading
import random

# Class to manage the server and client connections
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
        print("Le serveur attend des connexions...")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connexion acceptée de {client_address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        # Player chooses or creates a game
        partie = self.choisir_partie(client_socket)
        if partie is None:
            client_socket.close()
            return

        client_socket.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
        nom_client = client_socket.recv(1024).decode().strip()

        with self.lock:
            joueur_id = len(partie.joueurs) + 1
            partie.ajouter_joueur(nom_client, client_socket, joueur_id)
            print(f"{nom_client} (ID: {joueur_id}) a rejoint la partie {partie.id_partie}")

            # Start the game if it's not already started
            if not partie.jeu_commence:
                partie.commencer_partie()
                print(f"Partie {partie.id_partie} commence avec {len(partie.joueurs)} joueur(s).")

        partie.gerer_client(client_socket, nom_client)

    def choisir_partie(self, client_socket):
        while True:  # Loop until a valid choice is made
            # Display available games
            if self.parties:
                client_socket.send("Parties disponibles :\n".encode())
                for id_partie, partie in self.parties.items():
                    status = "commencée" if partie.jeu_commence else "non commencée"
                    client_socket.send(f"Partie {id_partie} ({status}) \n".encode())
            else:
                client_socket.send("Aucune partie disponible. Vous pouvez créer une nouvelle partie.\n".encode())

            client_socket.send("Tapez l'ID de la partie pour la rejoindre ou 'nouvelle' pour en créer une : ".encode())
            choix = client_socket.recv(1024).decode().strip()

            # If the user chooses to create a new game
            if choix.lower() == "nouvelle":
                with self.lock:
                    id_partie = self.next_game_id
                    partie = Partie(id_partie)
                    self.parties[id_partie] = partie
                    self.next_game_id += 1
                client_socket.send(f"Nouvelle partie {id_partie} créée.\n".encode())
                return partie

            # If the user chooses an existing game
            try:
                id_partie = int(choix)
                if id_partie in self.parties:
                    partie = self.parties[id_partie]
                    if partie.jeu_commence:
                        client_socket.send("La partie a déjà commencé. Veuillez choisir une autre partie ou créer une nouvelle.\n".encode())
                    else:
                        client_socket.send(f"Vous avez rejoint la partie {id_partie}.\n".encode())
                        return partie
                else:
                    client_socket.send("Partie invalide. Veuillez réessayer.\n".encode())
            except ValueError:
                client_socket.send("Entrée non valide. Veuillez réessayer.\n".encode())

class Partie:
    def __init__(self, id_partie):
        self.id_partie = id_partie
        self.joueurs = {}
        self.tours_termines = 0
        self.jeu_commence = False
        self.scores = {}
        self.sockets = {}

    def ajouter_joueur(self, nom, client_socket, joueur_id):
        self.joueurs[nom] = joueur_id
        self.sockets[nom] = client_socket

    def commencer_partie(self):
        self.jeu_commence = True

    def terminer_partie(self):
        gagnant = max(self.scores, key=self.scores.get)
        for nom_client, client_socket in self.sockets.items():
            if nom_client == gagnant:
                client_socket.send(f"Félicitations {nom_client}, vous avez gagné avec un score de {self.scores[nom_client]} points !\n".encode())
            else:
                client_socket.send(f"Le gagnant est {gagnant} avec un score de {self.scores[gagnant]} points.\n".encode())
            client_socket.close()

    def gerer_client(self, client_socket, nom_client):
        total_score = 0
        for tour in range(6):
            points = self.tour_de_jeu(client_socket, nom_client)
            total_score += points
            client_socket.send(f"Tour {tour + 1} terminé. Score actuel : {total_score}.\n".encode())
        
        # Record total score for this player
        with threading.Lock():
            self.scores[nom_client] = total_score
            self.tours_termines += 1
            if self.tours_termines == len(self.joueurs):
                self.terminer_partie()

    def tour_de_jeu(self, client_socket, nom):
        des = self.lancer_des()
        client_socket.send(f"{nom}, Premier lancer : {des}\n".encode())
        
        lancers = 1
        valeur_gardee = None

        while lancers < 3:
            client_socket.send(f"{nom}, Entrez la valeur des dés à garder (ex: 5) ou tapez 'fin' pour ne pas relancer : ".encode())
            choix = client_socket.recv(1024).decode().strip()

            if choix.lower() == "fin":
                break

            try:
                valeur_gardee = int(choix)
                if valeur_gardee in des:
                    des = self.relancer_des(des, valeur_gardee)
                    lancers += 1
                    client_socket.send(f"{nom}, Lancer suivant : {des}\n".encode())
                else:
                    client_socket.send(f"Entrée non valide, la valeur {valeur_gardee} ne fait pas partie des dés {des}. Lancer actuel : {des}\n".encode())
            except ValueError:
                client_socket.send(f"Entrée non valide, veuillez entrer un chiffre valide. Lancer actuel : {des}\n".encode())

        points = des.count(valeur_gardee) * valeur_gardee if valeur_gardee else sum(des)
        client_socket.send(f"{nom}, Vous avez marqué {points} points pour ce tour.\n".encode())
        
        return points

    @staticmethod
    def lancer_des():
        return [random.randint(1, 6) for _ in range(5)]

    @staticmethod
    def relancer_des(des, valeur_gardee):
        for i in range(len(des)):
            if des[i] != valeur_gardee:
                des[i] = random.randint(1, 6)
        return des

if __name__ == "__main__":
    server = Server()
    server.start()
