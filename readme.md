# Struttura

- pollsAPI è l'applicazione che implementa le API.
    - Gli endpoint sono raggiungibili a partire dal seguente [indirizzo](https://ppmproject-production.up.railway.app/api/).
    - Dall'indirizzo root è disponibile la visualizzazione classica delle API di DRF attraverso DefaultRouter
    - Una documentazione più dettagliata dei vari endpoint è stata realizzata tramite Swagger ed è disponibile al seguente [link](https://ppmproject-production.up.railway.app/swagger/)
        - All'interno della documentazione Swagger, per ogni richiesta, è possibile leggere i permessi necessari per effettuarla, i parametri richiesti nel corpo ed i tipi di response previsti
        - Per autenticarsi è sufficiente fare una richiesta agli endpoint Register o Login, i quali permettono di ricevere una stringa token da inserire al momento dell'autenticazione come "Token stringa_token".
        - Per accedere all'autenticazione è necessario premere sull'icona del lucchetto ed inserire la stringa descritta precedentemente
- polls è l'applicazione che si occupa di gestire un esempio di client che effettua richieste a pollsAPI
    - La pagina iniziale è accessibile all'[indirizzo di base del progetto](https://ppmproject-production.up.railway.app/)
    - Le pagine del client sono realizzate attraverso viste, templates e forms
    - Attraverso il client è possibile:
        - Senza effettuare l'accesso è possibile solamente visualizzare i sondaggi ed i loro risultati
        - Per registrarsi è necessario fornire un'email ed un username non ancora utilizzati, nel login è possibile inserire sia l'username che l'email come info
        - Successivamente all'autenticazione verranno salvati nella sessione i dati dell'utente (token, username ed email), i quali verranno cancellati effettuando il log out o chiudendo il browser
        - Effettuando l'accesso attraverso login o registrazione è possibile votare i sondaggi (un solo voto per utente per ogni sondaggio) o accedere al proprio profilo
        - Dal proprio profilo è possibile visualizzare le proprie informazioni, i sondaggi creati e quelli votati
        - Dai sondaggi creati è possibile modificare alcuni parametri dei sondaggi (domanda, proprietario e scelte), eliminare sondaggi o crearne di nuovi (inserendo gli stessi parametri disponibili nella modifica)