import socket
import threading
import random

class ServeurJeu:
    def __init__(self, hote='localhost', port=2410):
        self.hote = hote
        self.port = port
        self.socket_serveur = None
        self.lock = threading.Lock()
        self.parties = {}  # {id_partie: {"nom": nom_partie, "joueurs": [], "chat": [], "scores": {}}}
        self.prochain_id_partie = 1
        self.joueurs=0
        self.partieterminee=0

    def lancer_des(self):
        return [random.randint(1, 6) for _ in range(5)]

    def relancer_des(self, des, valeur_gardee):
        for i in range(len(des)):
            if des[i] != valeur_gardee:
                des[i] = random.randint(1, 6)
        return des

    def diffuser_message(self, id_partie, message, emetteur=None):
        """Diffuser un message à tous les joueurs d'une même partie."""
        with self.lock:
            for joueur in self.parties[id_partie]["joueurs"]:
                if joueur != emetteur:
                    try:
                        joueur.send(f"[Chat - Partie {id_partie}] {message}".encode())
                    except:
                        self.parties[id_partie]["joueurs"].remove(joueur)

    def partie(self, socket_client, nom_client, id_partie):
        """Gérer la partie d'un joueur."""
        print(f"Début de la partie {id_partie} pour {nom_client}")
        socket_client.send(f"Bienvenue dans la partie '{self.parties[id_partie]['nom']}', {nom_client} !\n".encode())

        points_totaux = 0

        # Marquer la partie comme commencée au premier lancer de dés
        with self.lock:
            if not self.parties[id_partie]["commence"]:
                self.parties[id_partie]["commence"] = True

        for tour in range(6):  # Chaque joueur joue 6 tours
            des = self.lancer_des()
            socket_client.send(f"\nTour {tour + 1} : Vous avez lancé {des}\n".encode())

            lancer = 1  # Compteur de lancers
            while lancer < 3:
                socket_client.send("Entrez une valeur à garder ou tapez 'fin' pour terminer le tour, ou 'message: <votre message>' pour discuter : ".encode())
                choix = socket_client.recv(1024).decode().strip()

                # Gestion des messages de chat
                if choix.startswith("message:"):
                    contenu = choix.replace("message:", "").strip()
                    self.diffuser_message(id_partie, f"{nom_client} : {contenu}", socket_client)
                    continue

                # Si le joueur termine le tour
                if choix.lower() == "fin":
                    break

                # Gestion du lancer des dés
                try:
                    valeur_gardee = int(choix)
                    if valeur_gardee in des:
                        des = self.relancer_des(des, valeur_gardee)
                        socket_client.send(f"Résultat après relance : {des}\n".encode())
                        lancer += 1  # Incrémenter uniquement après un lancer valide
                    else:
                        socket_client.send(f"Valeur non valide, essayez encore.\n".encode())
                except ValueError:
                    socket_client.send(f"Entrée invalide. Veuillez entrer un nombre ou 'fin'.\n".encode())
            
            # Calcul des points pour ce tour
            points = sum(des)
            points_totaux += points
            socket_client.send(f"Points pour ce tour : {points}\n".encode())
        
        with self.lock:
            # Stocker le score total du joueur
            self.parties[id_partie]["scores"][nom_client] = points_totaux
            self.parties[id_partie]["joueurs_termine"] += 1

            # Vérifier si tous les joueurs de cette partie ont terminé
            if self.parties[id_partie]["joueurs_termine"] == len(self.parties[id_partie]["joueurs"]):
                print(f"Tous les joueurs de la partie {id_partie} ont terminé.")
                self.annoncer_gagnant(id_partie)

        socket_client.send(f"Partie terminée ! Votre score total : {points_totaux}\n".encode())

    def annoncer_gagnant(self, id_partie):
        """Annonce le gagnant de la partie."""
        scores = self.parties[id_partie]["scores"]
        gagnant = max(scores, key=scores.get)
        score_gagnant = scores[gagnant]

        message_gagnant = f"Le gagnant de la partie '{self.parties[id_partie]['nom']}' est {gagnant} avec un score de {score_gagnant} points !"
        print(message_gagnant)
        

        # Diffuser le message à tous les joueurs
        for joueur in self.parties[id_partie]["joueurs"]:
            try:
                joueur.send(f"{message_gagnant}\n".encode())
            except:
                continue


        # Supprimer la partie terminée
        del self.parties[id_partie]


    def gerer_connexion_client(self, socket_client):
        """Gérer la connexion des clients."""
        socket_client.send("Bienvenue au serveur de jeu ! Voici les parties disponibles :\n".encode())

        while True:  # Boucle pour permettre au joueur de réessayer
            with self.lock:
                for id_partie, infos_partie in self.parties.items():
                    socket_client.send(f"ID: {id_partie} | Nom: {infos_partie['nom']} | Commencée : {'Oui' if infos_partie['commence'] else 'Non'}\n".encode())

            socket_client.send("Tapez l'ID de la partie que vous souhaitez rejoindre, ou 'new' pour créer une nouvelle partie, ou 'quit' pour quitter : ".encode())
            choix = socket_client.recv(1024).decode().strip()

            with self.lock:
                if choix.lower() == "new":
                    # Créer une nouvelle partie
                    nom_partie = f"Partie {self.prochain_id_partie}"
                    self.parties[self.prochain_id_partie] = {
                        "nom": nom_partie,
                        "joueurs": [],
                        "chat": [],
                        "scores": {},
                        "commence": False,
                        "joueurs_termine": 0, 
                    }
                    id_partie = self.prochain_id_partie
                    self.prochain_id_partie += 1
                    socket_client.send(f"Nouvelle partie créée : {nom_partie} (ID: {id_partie})\n".encode())
                elif choix.lower() == "quit":
                    socket_client.send("Vous avez quitté le serveur de jeu. À bientôt !\n".encode())
                    socket_client.close()
                    return
                else:
                    try:
                        id_partie = int(choix)
                        if id_partie not in self.parties:
                            socket_client.send("ID de partie invalide.\n".encode())
                            continue

                        # Vérifier si la partie a déjà commencé
                        if self.parties[id_partie]["commence"]:
                            socket_client.send("La partie a déjà commencé. Vous ne pouvez pas la rejoindre.\n".encode())
                            continue
                    except ValueError:
                        socket_client.send("Entrée invalide. Veuillez entrer un ID valide, 'new' pour créer une partie, ou 'quit' pour quitter.\n".encode())
                        continue

            socket_client.send("Veuillez entrer votre nom : ".encode())
            nom_client = socket_client.recv(1024).decode().strip()

            with self.lock:
                # Ajouter le joueur à la partie après avoir obtenu son nom
                self.parties[id_partie]["joueurs"].append(socket_client)

            # Lancer un thread pour gérer la partie
            threading.Thread(target=self.partie, args=(socket_client, nom_client, id_partie)).start()
            break

    def demarrer_serveur(self):
        """Démarrer le serveur."""
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.bind((self.hote, self.port))
        self.socket_serveur.listen(5)
        print("Le serveur est prêt. En attente de connexions...")

        while True:
            socket_client, _ = self.socket_serveur.accept()
            threading.Thread(target=self.gerer_connexion_client, args=(socket_client,)).start()
            self.joueurs += 1


if __name__ == "__main__":
    serveur = ServeurJeu()
    serveur.demarrer_serveur()
