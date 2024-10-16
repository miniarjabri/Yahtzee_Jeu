import socket  

# Fonction principale pour jouer
def jouer():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    
    while True:
        # Recevoir les messages du serveur
        message = client_socket.recv(1024).decode()
        print(message)
        
        # Si le serveur demande le nom du joueur
        if "nom" in message:
            choix = input("Entrez votre nom : ")
            client_socket.send(choix.encode())
        
        # Si la partie est terminée pour ce joueur, attendre les autres joueurs
        elif "Partie terminée" in message:
            print("En attente des autres joueurs...")
        
        # Si c'est l'annonce du gagnant, on ferme la connexion
        elif "Le gagnant est" in message:
            print("Annonce du gagnant reçue, fermeture de la connexion.")
            break
        
        # Si le serveur attend une réponse (lancer des dés, choix de relance, etc.)
        elif "lancer" in message or "figure" in message:
            choix = input("Entrez votre choix : ")
            client_socket.send(choix.encode())

    client_socket.close()

# Point d'entrée du programme
if __name__ == "__main__":
    jouer()  # Lancer le jeu client
