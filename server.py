import socket
import threading
import random

class ServeurJeu:
    def __init__(self, hote='localhost', port=2410):
        self.hote = hote
        self.port = port
        self.socket_serveur = None
        self.jeu_commence = False
        self.lock = threading.Lock()
        self.noms_joueurs = []
        self.joueurs_ids = {}
        self.prochain_id_joueur = 1
        self.nombre_clients_connectes = 0
        self.tours_termines = 0
        self.scores = {}
        self.sockets = {}
        self.clients = []  # Liste des sockets clients pour le chat

    def lancer_des(self):
        return [random.randint(1, 6) for _ in range(5)]

    def relancer_des(self, des, valeur_gardee):
        for i in range(len(des)):
            if des[i] != valeur_gardee:
                des[i] = random.randint(1, 6)
        return des

    def diffuser_message(self, message, emetteur=None):
        """Diffuser un message à tous les clients sauf l'émetteur."""
        with self.lock: # seul un thread à la fois accède ou modifie la liste des clients
            for client in self.clients:
                if client != emetteur:
                    try:
                        client.send(f"[Chat] {message}".encode())
                    except:
                        self.clients.remove(client) # si un client se déconnecte il est retiré de la liste

    def partie(self, socket_client, nom_client, id_joueur):
        """Gère une partie complète pour un joueur."""
        print(f"Début de la partie pour {nom_client} (ID: {id_joueur})")
        socket_client.send(f"Joueur {id_joueur} ({nom_client}), vous avez commencé la partie.\n".encode())
        points_totaux = 0

        for tour in range(6):  # Chaque joueur joue 6 tours
            des = self.lancer_des()
            socket_client.send(f"Tour {tour + 1} : Vous avez lancé {des}\n".encode())
            choix = None

            for lancer in range(3):  # Dans chaque tour il y a 3 lancers
                socket_client.send(f"Entrez une valeur à garder ou tapez 'fin' pour arrêter, ou 'message: <votre message>' pour discuter : ".encode())
                while True:
                    try:
                        choix = socket_client.recv(1024).decode().strip()

                        # Vérifier si c'est un message de chat
                        if choix.startswith("message:"):
                            contenu = choix.replace("message:", "").strip()
                            self.diffuser_message(f"{nom_client} : {contenu}", socket_client)
                        elif choix.lower() == "fin":
                            break
                        else:
                            valeur_gardee = int(choix)
                            if valeur_gardee in des:
                                des = self.relancer_des(des, valeur_gardee)
                                socket_client.send(f"Résultat après relance : {des}\n".encode())
                            else:
                                socket_client.send(f"Valeur non valide, essayez encore.\n".encode())
                    except ValueError:
                        socket_client.send(f"Entrée invalide, veuillez entrer un nombre, 'fin', ou 'message: <votre message>'.\n".encode())
                        continue
                    break

            points = des.count(int(choix)) * int(choix) if choix.isdigit() else sum(des)
            points_totaux += points
            socket_client.send(f"Points pour ce tour : {points}\n".encode())

        print(f"{nom_client} a terminé la partie avec un score total de {points_totaux}.")
        socket_client.send(f"Partie terminée ! Votre score total : {points_totaux}\n".encode())
        return points_totaux

    def gerer_client(self, socket_client, nom_client, id_joueur):
        """Gère les interactions avec un client et la progression du jeu."""
        try:
            # Gérer une partie pour ce joueur
            score_total = self.partie(socket_client, nom_client, id_joueur)
            self.scores[nom_client] = score_total
            self.sockets[nom_client] = socket_client

            with self.lock:
                self.tours_termines += 1
                if self.tours_termines == len(self.noms_joueurs):
                    self.terminer_jeu()
                else:
                    socket_client.send(f"{nom_client}, vous avez terminé vos tours. Veuillez attendre les autres joueurs.\n".encode())

        except (ConnectionResetError, BrokenPipeError):
            print(f"Le client {nom_client} s'est déconnecté.")
        finally:
            self.clients.remove(socket_client)

    def terminer_jeu(self):
        """Clôture le jeu et informe les joueurs du gagnant."""
        gagnant = max(self.scores, key=self.scores.get)
        for nom_client, socket_client in self.sockets.items():
            try:
                if nom_client == gagnant:
                    socket_client.send(f"Félicitations {nom_client}, vous avez gagné avec un score de {self.scores[nom_client]} points !\n".encode())
                else:
                    socket_client.send(f"Désolé {nom_client}, vous avez perdu. Le gagnant est {gagnant} avec un score de {self.scores[gagnant]} points.\n".encode())
            finally:
                socket_client.close()
        print("Le jeu est terminé et tous les clients ont été déconnectés.")

    def gerer_connexion_client(self, socket_client):
        """Traite la connexion des clients."""
        with self.lock:
            if self.jeu_commence:
                socket_client.send("Désolé, le jeu a déjà commencé. Vous ne pouvez pas rejoindre.\n".encode())
                socket_client.close()
                return

            self.nombre_clients_connectes += 1
            self.clients.append(socket_client)

        socket_client.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
        nom_client = socket_client.recv(1024).decode().strip()

        with self.lock:
            id_joueur = self.prochain_id_joueur
            self.joueurs_ids[nom_client] = id_joueur
            self.noms_joueurs.append(nom_client)
            self.prochain_id_joueur += 1

            if not self.jeu_commence:
                self.jeu_commence = True

        self.gerer_client(socket_client, nom_client, id_joueur)

    def demarrer_serveur(self):
        """Démarre le serveur et gère les clients."""
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.bind((self.hote, self.port))
        self.socket_serveur.listen(5)
        print("Le serveur attend des connexions...")

        while True:
            socket_client, adresse_client = self.socket_serveur.accept()
            threading.Thread(target=self.gerer_connexion_client, args=(socket_client,)).start()

if __name__ == "__main__": # Point d'entrée pour l'exécution du code
    serveur = ServeurJeu()
    serveur.demarrer_serveur()
