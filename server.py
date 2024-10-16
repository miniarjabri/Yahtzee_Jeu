import socket
import random
import threading

# Fonction qui lance 5 dés et retourne une liste de résultats
def lancer_des():
    return [random.randint(1, 6) for _ in range(5)]

def relancer_des(des, valeur_gardee):
    """
    Relancer les dés qui ne correspondent pas à la valeur gardée.
    Si la valeur gardée est par exemple 5, seuls les dés qui ne sont pas 5 seront relancés.
    """
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
def partie(client_socket, nom):
    total_points = 0

    for tour in range(6):  # 6 tours pour la partie
        client_socket.send(f"{nom}, Tour {tour + 1} - Lancer les dés\n".encode())
        points = tour_de_jeu(client_socket, nom)  # Gérer un tour complet
        total_points += points  # Ajouter les points au total
    
    # Afficher le tableau des scores final après 6 tours
    client_socket.send(f"{nom}, Partie terminée ! Score total : {total_points}\n".encode())
    
    return total_points

# Fonction pour gérer les clients simultanément
def gerer_client(client_socket, nom_client, scores, sockets):
    total_score = partie(client_socket, nom_client)  # Lancer une partie complète pour le joueur
    scores[nom_client] = total_score  # Ajouter le score final au dictionnaire des scores
    sockets[nom_client] = client_socket  # Stocker le socket pour ce client
    
    # Ne fermez pas la connexion ici, attendez que tous les joueurs aient terminé
    client_socket.send(f"{nom_client}, vous avez terminé vos tours. Veuillez attendre les autres joueurs.\n".encode())

# Fonction principale qui démarre le serveur et gère plusieurs clients
def demarrer_serveur():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    print("Le serveur attend des connexions...")

    clients = []
    scores = {}
    sockets = {}  # Nouveau dictionnaire pour stocker les sockets

    while len(clients) < 3:  # On attend 3 clients pour démarrer une partie
        client_socket, client_address = server_socket.accept()
        print(f"Connexion acceptée de {client_address}")

        # Demander le nom du client
        client_socket.send("Bienvenue au jeu de Yahtzee ! Veuillez entrer votre nom : ".encode())
        nom_client = client_socket.recv(1024).decode().strip()

        # Démarrer un thread pour chaque client
        client_thread = threading.Thread(target=gerer_client, args=(client_socket, nom_client, scores, sockets))
        client_thread.start()
        clients.append(client_thread)

    # Attendre que tous les clients aient terminé
    for client in clients:
        client.join()

    # Déterminer le gagnant
    gagnant = max(scores, key=scores.get)
    print(f"Le gagnant est {gagnant} avec un score de {scores[gagnant]} points !")

    # Envoyer le résultat final à tous les clients
    for nom_client, client_socket in sockets.items():
        client_socket.send(f"Le gagnant est {gagnant} avec un score de {scores[gagnant]} points !\n".encode())
        client_socket.close()  # Fermer la connexion après avoir envoyé le message final

if __name__ == "__main__":
    demarrer_serveur()  # Démarrer le serveur
