import socket  

# Point d'entrée du programme
def jouer():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    while True:
        # Recevoir les messages du serveur
        message = client_socket.recv(1024).decode()
        print(message)
        if "Partie terminée" in message:
            break
        # Si le serveur attend une réponse (relance des dés ou choix de figure)
        if "lancer" in message or "figure" in message:
            choix = input("Entrez votre choix : ")
            client_socket.send(choix.encode())

    client_socket.close()
# Point d'entrée du programme
if __name__ == "__main__":
    jouer()  # Lancer le jeu client