## Istruzioni 

1. Caricare l’immagine Docker del grader:
   docker load -i lab-grader-esonero-1:1.0.1.tar

2. Avviare il proprio progetto:
   docker compose up --build -d

3. Eseguire il grader passando la propria matricola:
   docker run --network host lab-grader-esonero-1:1.0.1 <vostra_matricola>

0. Per annullare il tentativo precedente
   docker compose down




  
