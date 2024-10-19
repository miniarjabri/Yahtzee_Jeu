import socket

# Fonction principale pour jouer
def jouer():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(('localhost', 12345))
    except ConnectionRefusedError:
        print("Connexion refusée par le serveur.")
        return

    while True:
        # Recevoir les messages du serveur
        message = client_socket.recv(1024).decode()

        if not message:  # Si le message est vide, arrêter la boucle
            print("Connexion fermée par le serveur.")
            break

        print(f"Message du serveur : {message}")  # Debug pour vérifier ce que le serveur envoie

        if "nom" in message:
            choix = input("Entrez votre nom : ")
            client_socket.send(choix.encode())

        elif "ID de la partie" in message:
            choix = input("Entrez votre choix : ")
            client_socket.send(choix.encode())

        elif "Vous avez rejoint" in message or "Nouvelle partie" in message:
            print(message)

        # Cas où le joueur doit choisir une valeur de dé à garder ou taper 'fin'
        elif "valeur des dés à garder" in message:
            choix = input("Entrez la valeur des dés à garder (ex: 5) ou tapez 'fin' : ")  # Saisie pour garder un dé
            client_socket.send(choix.encode())

        # Cas où le jeu est terminé ou pour envoyer des réponses "oui"/"non"
        elif "relancer" in message or "terminer" in message:
            choix = input("Entrez 'oui' ou 'non' : ")  # Saisie pour relancer ou non
            client_socket.send(choix.encode())

    client_socket.close()

# Point d'entrée du programme
if __name__ == "__main__":
    jouer()  # Lancer le jeu client
