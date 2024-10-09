import socket
import random

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
def tour_de_jeu(client_socket):
    des = lancer_des()  # Premier lancer de dés
    client_socket.send(f"Premier lancer : {des}\n".encode())

    lancers = 1  # Premier lancer déjà fait

    while lancers < 3:  # Maximum de 3 lancers
        client_socket.send("Entrez la valeur des dés à garder (ex: 5) ou tapez 'fin' pour ne pas relancer : ".encode())
        choix = client_socket.recv(1024).decode().strip()  # Réception de la valeur des dés à garder ou 'fin'
        
        if choix == "fin":  # Si le joueur ne veut pas relancer, il peut taper 'fin'
            break

        # Convertir la valeur choisie en un entier
        try:
            valeur_gardee = int(choix)  # La valeur des dés à garder doit être un entier
            if 1 <= valeur_gardee <= 6:  # Vérifier que la valeur est valide
                des = relancer_des(des, valeur_gardee)  # Relancer les dés qui ne correspondent pas à la valeur gardée
                lancers += 1  # Compter un lancer supplémentaire
                client_socket.send(f"Lancer suivant : {des}\n".encode())  # Envoyer les nouveaux dés
            else:
                client_socket.send(f"Entrée non valide, veuillez entrer une valeur entre 1 et 6. Lancer actuel : {des}\n".encode())
        except ValueError:
            client_socket.send(f"Entrée non valide, veuillez entrer un chiffre valide. Lancer actuel : {des}\n".encode())

    # Calcul du score pour ce tour (somme des dés ou, si une valeur a été gardée, multiplier cette valeur)
    if choix != "fin":
        points = des.count(valeur_gardee) * valeur_gardee  # Points pour la valeur gardée (nombre de dés * valeur)
    else:
        points = sum(des)  # Si 'fin' a été choisi, calculer la somme des dés

    client_socket.send(f"Vous avez marqué {points} points pour ce tour.\n".encode())
    
    return points

# Fonction qui gère la partie complète (6 tours)
def partie(client_socket):
    total_points = 0

    for tour in range(6):  # 6 tours pour la partie
        client_socket.send(f"Tour {tour + 1} - Lancer les dés\n".encode())
        points = tour_de_jeu(client_socket)  # Gérer un tour complet
        total_points += points  # Ajouter les points au total
    
    # Afficher le tableau des scores final après 6 tours
    client_socket.send(f"Partie terminée ! Score total : {total_points}\n".encode())
    
    return total_points

def demarrer_serveur():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    print("Le serveur attend des connexions...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connexion acceptée de {client_address}")
        
        total_score = partie(client_socket)  # Lancer une partie complète pour le joueur
        client_socket.send(f"Votre score final est de {total_score} points.\n".encode())
        
        client_socket.close()

if __name__ == "__main__":
    demarrer_serveur()  # Démarrer le serveur
