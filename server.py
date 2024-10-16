import socket
import threading
import random

# Variable pour indiquer si le jeu a déjà commencé
jeu_commence = False
lock = threading.Lock()

# Liste pour suivre les noms et IDs des joueurs
noms_joueurs = []
joueurs_ids = {}
next_player_id = 1  # Compteur d'ID des joueurs
nombre_clients_connectes = 0  # Compteur du nombre de clients connectés
tours_termines = 0  # Compteur pour les joueurs ayant terminé leur tour

# Fonction qui lance 5 dés et retourne une liste de résultats
def lancer_des():
    return [random.randint(1, 6) for _ in range(5)]

def relancer_des(des, valeur_gardee):
    for i in range(len(des)):
        if des[i] != valeur_gardee:
            des[i] = random.randint(1, 6)
    return des

# Fonction qui gère un tour de jeu (3 lancers par tour)
def tour_de_jeu(client_socket, nom):
    des = lancer_des()  # Premier lancer de dés
    client_socket.send(f"{nom}, Premier lancer : {des}\n".encode())

    lancers = 1  # Premier lancer déjà fait

    while lancers < 3:  # Maximum de 3 lancers
        client_socket.send(f"{nom}, Entrez la valeur des dés à garder (ex: 5) ou tapez 'fin' pour ne pas relancer : ".encode())
        choix = client_socket.recv(1024).decode().strip()  # Réception de la valeur des dés à garder ou 'fin'
        
        if choix == "fin":  # Si le joueur ne veut pas relancer, il peut taper 'fin'
            break

        # Convertir la valeur choisie en un entier
        try:
            valeur_gardee = int(choix)  # La valeur des dés à garder doit être un entier
            if 1 <= valeur_gardee <= 6:  # Vérifier que la valeur est valide
                des = relancer_des(des, valeur_gardee)  # Relancer les dés qui ne correspondent pas à la valeur gardée
                lancers += 1  # Compter un lancer supplémentaire
                client_socket.send(f"{nom}, Lancer suivant : {des}\n".encode())  # Envoyer les nouveaux dés
            else:
                client_socket.send(f"Entrée non valide, veuillez entrer une valeur entre 1 et 6. Lancer actuel : {des}\n".encode())
        except ValueError:
            client_socket.send(f"Entrée non valide, veuillez entrer un chiffre valide. Lancer actuel : {des}\n".encode())

    # Calcul du score pour ce tour (somme des dés ou, si une valeur a été gardée, multiplier cette valeur)
    if choix != "fin":
        points = des.count(valeur_gardee) * valeur_gardee  # Points pour la valeur gardée (nombre de dés * valeur)
    else:
        points = sum(des)  # Si 'fin' a été choisi, calculer la somme des dés

    client_socket.send(f"{nom}, Vous avez marqué {points} points pour ce tour.\n".encode())
    
    return points

# Fonction qui gère la partie complète pour un joueur
def partie(client_socket, nom, joueur_id):
    client_socket.send(f"Joueur {joueur_id} ({nom}), vous avez commencé la partie.\n".encode())
    total_points = 0

    for tour in range(3):  # Chaque joueur joue 3 tours
        points = tour_de_jeu(client_socket, nom)
        total_points += points
    
    client_socket.send(f"{nom}, Partie terminée ! Score total : {total_points}\n".encode())
    
    return total_points

# Fonction pour gérer les clients simultanément
def gerer_client(client_socket, nom_client, scores, sockets, joueur_id):
    global tours_termines
    try:
        total_score = partie(client_socket, nom_client, joueur_id)
        scores[nom_client] = total_score
        sockets[nom_client] = client_socket
        client_socket.send(f"{nom_client}, vous avez terminé vos tours. Veuillez attendre les autres joueurs.\n".encode())

        with lock:
            tours_termines += 1
            print(f"Joueurs ayant terminé: {tours_termines}/{len(noms_joueurs)}")
            if tours_termines == len(noms_joueurs):
                # Tous les joueurs ont terminé, on peut clôturer la partie
                terminer_jeu(scores, sockets)

    except (ConnectionResetError, BrokenPipeError):
        print(f"Le client {nom_client} s'est déconnecté.")
    finally:
        pass  # Ne pas fermer la connexion immédiatement

# Fonction pour terminer le jeu et informer les joueurs du gagnant
def terminer_jeu(scores, sockets):
    # Déterminer le gagnant
    gagnant = max(scores, key=scores.get)
    print(f"Le gagnant est {gagnant} avec un score de {scores[gagnant]} points !")

    # Informer tous les clients du gagnant
    for nom_client, client_socket in sockets.items():
        try:
            if nom_client == gagnant:
                client_socket.send(f"Félicitations {nom_client}, vous avez gagné avec un score de {scores[nom_client]} points !\n".encode())
            else:
                client_socket.send(f"Malheureusement {nom_client}, vous avez perdu. Le gagnant est {gagnant} avec un score de {scores[gagnant]} points.\n".encode())
        except Exception as e:
            print(f"Erreur lors de l'envoi au client {nom_client}: {e}")
        finally:
            client_socket.close()

# Fonction pour traiter la connexion des clients
def handle_client(client_socket, scores, sockets):
    global next_player_id, jeu_commence, nombre_clients_connectes

    # Si le jeu a déjà commencé, renvoyer un message d'erreur
    with lock:
        if jeu_commence:
            client_socket.send("Désolé, le jeu a déjà commencé. Vous ne pouvez pas rejoindre.\n".encode())
            client_socket.close()
            return

        nombre_clients_connectes += 1
        print(f"Nombre de clients connectés: {nombre_clients_connectes}")

    client_socket.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
    nom_client = client_socket.recv(1024).decode().strip()

    with lock:
        joueur_id = next_player_id
        joueurs_ids[nom_client] = joueur_id
        noms_joueurs.append(nom_client)
        next_player_id += 1
        print(f"{nom_client} (ID: {joueur_id}) s'est connecté. Nombre total de joueurs: {len(noms_joueurs)}")

        # Associer chaque socket à un joueur ici
        sockets[nom_client] = client_socket

        # Le jeu commence dès qu'un joueur entre son nom
        if not jeu_commence:
            jeu_commence = True
            print(f"Le jeu commence avec {nombre_clients_connectes} joueurs.")
    
    # Lancer la partie pour ce joueur
    gerer_client(client_socket, nom_client, scores, sockets, joueur_id)

# Fonction principale qui démarre le serveur et gère plusieurs clients
def demarrer_serveur():
    global jeu_commence
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    print("Le serveur attend des connexions...")

    clients_threads = []
    scores = {}
    sockets = {}

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connexion acceptée de {client_address}")

        # Lancer un thread pour gérer le client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, scores, sockets))
        client_thread.start()
        clients_threads.append(client_thread)

    # Attendre que tous les clients aient fini de jouer
    for client_thread in clients_threads:
        client_thread.join()

if __name__ == "__main__":
    demarrer_serveur()
