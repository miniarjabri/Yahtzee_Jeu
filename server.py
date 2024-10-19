import socket
import threading
import random

# Dictionnaire pour stocker les différentes parties
parties = {}
lock = threading.Lock()
next_game_id = 1

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

# Fonction pour lancer une nouvelle partie ou rejoindre une existante
def choisir_partie(client_socket):
    global next_game_id

    with lock:
        # Envoyer la liste des parties en attente
        if parties:
            client_socket.send("Parties disponibles :\n".encode())
            for id_partie, partie in parties.items():
                if partie.jeu_commence:
                    client_socket.send(f"Partie {id_partie} (commencée) avec {len(partie.joueurs)} joueur(s)\n".encode())
                else:
                    client_socket.send(f"Partie {id_partie} (non commencée) avec {len(partie.joueurs)} joueur(s)\n".encode())
        else:
            client_socket.send("Aucune partie disponible. Vous pouvez créer une nouvelle partie.\n".encode())

        client_socket.send("Tapez l'ID de la partie pour la rejoindre ou 'nouvelle' pour en créer une : ".encode())
        choix = client_socket.recv(1024).decode().strip()

        # Si le joueur crée une nouvelle partie
        if choix.lower() == "nouvelle":
            id_partie = next_game_id
            partie = Partie(id_partie)
            parties[id_partie] = partie
            next_game_id += 1
            client_socket.send(f"Nouvelle partie {id_partie} créée.\n".encode())
            return partie

        # Si le joueur rejoint une partie existante
        else:
            try:
                id_partie = int(choix)
                if id_partie in parties:
                    partie = parties[id_partie]
                    if partie.jeu_commence:
                        client_socket.send("La partie a déjà commencé, vous ne pouvez pas la rejoindre.\n".encode())
                        return None
                    else:
                        client_socket.send(f"Vous avez rejoint la partie {id_partie}.\n".encode())
                        return partie
                else:
                    client_socket.send("Partie invalide.\n".encode())
                    return None
            except ValueError:
                client_socket.send("Entrée non valide.\n".encode())
                return None


# Fonction qui lance 5 dés et retourne une liste de résultats
def lancer_des():
    return [random.randint(1, 6) for _ in range(5)]

# Fonction qui relance les dés en fonction de la valeur gardée
def relancer_des(des, valeur_gardee):
    for i in range(len(des)):
        if des[i] != valeur_gardee:
            des[i] = random.randint(1, 6)
    return des

# Fonction qui gère un tour de jeu avec choix de la valeur à garder
def tour_de_jeu(client_socket, nom):
    des = lancer_des()  # Premier lancer de dés
    client_socket.send(f"{nom}, Premier lancer : {des}\n".encode())

    lancers = 1  # Premier lancer déjà fait
    valeur_gardee = None  # Pour garder la valeur choisie

    while lancers < 3:  # Maximum de 3 lancers
        client_socket.send(f"{nom}, Entrez la valeur des dés à garder (ex: 5) ou tapez 'fin' pour ne pas relancer : ".encode())
        choix = client_socket.recv(1024).decode().strip()  # Réception de la valeur des dés à garder ou 'fin'
        
        if choix.lower() == "fin":  # Si le joueur ne veut pas relancer
            break

        # Convertir la valeur choisie en un entier et vérifier qu'elle appartient aux dés lancés
        try:
            valeur_gardee = int(choix)  # La valeur des dés à garder doit être un entier
            if valeur_gardee in des:  # Vérifier que la valeur appartient au lancer
                des = relancer_des(des, valeur_gardee)  # Relancer les dés qui ne correspondent pas à la valeur gardée
                lancers += 1  # Compter un lancer supplémentaire
                client_socket.send(f"{nom}, Lancer suivant : {des}\n".encode())  # Envoyer les nouveaux dés
            else:
                client_socket.send(f"Entrée non valide, la valeur {valeur_gardee} ne fait pas partie des dés {des}. Lancer actuel : {des}\n".encode())
        except ValueError:
            client_socket.send(f"Entrée non valide, veuillez entrer un chiffre valide. Lancer actuel : {des}\n".encode())

    # Calcul du score pour ce tour (somme des dés ou, si une valeur a été gardée, multiplier cette valeur)
    if valeur_gardee is not None:
        points = des.count(valeur_gardee) * valeur_gardee  # Points pour la valeur gardée (nombre de dés * valeur)
    else:
        points = sum(des)  # Si 'fin' a été choisi, calculer la somme des dés

    client_socket.send(f"{nom}, Vous avez marqué {points} points pour ce tour.\n".encode())
    
    return points

# Fonction principale qui gère la connexion d'un client
def handle_client(client_socket):
    global next_game_id

    # Demander au client de choisir ou créer une partie
    partie = None
    while not partie:
        partie = choisir_partie(client_socket)
    
    client_socket.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
    nom_client = client_socket.recv(1024).decode().strip()

    with lock:
        joueur_id = len(partie.joueurs) + 1
        partie.ajouter_joueur(nom_client, client_socket, joueur_id)
        print(f"{nom_client} (ID: {joueur_id}) a rejoint la partie {partie.id_partie}")

        # Si la partie n'a pas commencé, la démarrer dès qu'un joueur rejoint
        if not partie.jeu_commence:
            partie.commencer_partie()
            print(f"Partie {partie.id_partie} commence avec {len(partie.joueurs)} joueur(s).")
    
    gerer_client(client_socket, nom_client, partie)

# Fonction pour gérer les clients dans une partie spécifique
def gerer_client(client_socket, nom_client, partie):
    try:
        total_score = 0
        for tour in range(6):  # Chaque joueur joue 6 tours
            points = tour_de_jeu(client_socket, nom_client)
            total_score += points
            client_socket.send(f"Tour {tour + 1} terminé. Score actuel : {total_score}.\n".encode())
        
        # Enregistrer le score total pour ce joueur
        with lock:
            partie.scores[nom_client] = total_score
            partie.tours_termines += 1

            if partie.tours_termines == len(partie.joueurs):
                # Tous les joueurs ont terminé leurs tours
                partie.terminer_partie()
    except (ConnectionResetError, BrokenPipeError):
        print(f"Le client {nom_client} s'est déconnecté.")


# Fonction principale du serveur
def demarrer_serveur():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    print("Le serveur attend des connexions...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connexion acceptée de {client_address}")

        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    demarrer_serveur()