
build application et la base de données dans des container docker avec:

    docker-compose build

pour acceder au Dashboard un fois que l'API et bd sont en exécution:

    http://localhost:5000

Démarrer les clients avec le script squad_runner.py (voir le README dans le client):

dans un terminal python:

    python.exe squad_runner.py --count 5

le dashboard va recuperer la télémètrie des agents et l'afficher

après 10 cycle de la boucle infini des agents ils vont utiliser la route PUT /api/hosts/<int:agent_id>
pour changer leur status

fait CTRL-C pour terminer l'exécution de toutes les agents. Ceci va déclencher la consommation de la
route DELETE /api/hosts/<int:agent_id> est supprimer tout les agents de la base de données

documention par swagger disponible par http://localhost:5000/apidocs

les variables d'environement sont disponible par le fichier .env
