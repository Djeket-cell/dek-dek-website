// Animation du chat en pixel
class PixelCat {
    constructor() {
        this.messages = [
            "Bienvenue sur Dek.Dek ! 👋",
            "Découvrez nos livres inspirants ! 📚",
            "Explorez nos citations motivantes ! 💭",
            "Bonne lecture ! ✨",
            "Merci de votre visite ! 😊"
        ];
        this.currentMessageIndex = 0;
        this.isVisible = false;
        this.init();
    }

    init() {
        this.createCatElement();
        this.setupEventListeners();
        this.startWelcomeSequence();
    }

    createCatElement() {
        // Créer le conteneur principal
        this.container = document.createElement('div');
        this.container.className = 'pixel-cat-container';
        this.container.style.display = 'none';

        // Créer l'élément du chat
        this.catElement = document.createElement('div');
        this.catElement.className = 'pixel-cat';

        // Créer la bulle de dialogue
        this.speechBubble = document.createElement('div');
        this.speechBubble.className = 'speech-bubble';

        // Assembler les éléments
        this.container.appendChild(this.speechBubble);
        this.container.appendChild(this.catElement);
        document.body.appendChild(this.container);
    }

    setupEventListeners() {
        // Clic sur le chat
        this.container.addEventListener('click', () => {
            this.showNextMessage();
        });

        // Survol du chat
        this.container.addEventListener('mouseenter', () => {
            this.catElement.classList.add('waving');
            setTimeout(() => {
                this.catElement.classList.remove('waving');
            }, 1000);
        });

        // Auto-hide après inactivité
        let hideTimeout;
        document.addEventListener('mousemove', () => {
            if (this.isVisible) {
                clearTimeout(hideTimeout);
                hideTimeout = setTimeout(() => {
                    this.hideSpeechBubble();
                }, 5000);
            }
        });
    }

    startWelcomeSequence() {
        // Attendre un peu avant d'afficher le chat
        setTimeout(() => {
            this.showCat();
            setTimeout(() => {
                this.showWelcomeMessage();
            }, 1000);
        }, 2000);
    }

    showCat() {
        this.container.style.display = 'block';
        this.container.classList.add('entering');
        this.isVisible = true;

        // Retirer la classe d'animation après l'animation
        setTimeout(() => {
            this.container.classList.remove('entering');
        }, 1000);
    }

    showWelcomeMessage() {
        this.showMessage(this.messages[0]);
        this.catElement.classList.add('talking');
        
        setTimeout(() => {
            this.catElement.classList.remove('talking');
        }, 2000);
    }

    showMessage(message) {
        this.speechBubble.textContent = message;
        this.speechBubble.classList.add('show');
        
        // Cacher automatiquement après 4 secondes
        setTimeout(() => {
            this.hideSpeechBubble();
        }, 4000);
    }

    showNextMessage() {
        this.currentMessageIndex = (this.currentMessageIndex + 1) % this.messages.length;
        this.showMessage(this.messages[this.currentMessageIndex]);
        
        // Animation de parole
        this.catElement.classList.add('talking');
        setTimeout(() => {
            this.catElement.classList.remove('talking');
        }, 1500);
    }

    hideSpeechBubble() {
        this.speechBubble.classList.remove('show');
    }

    // Méthode pour changer les messages selon la page
    setMessages(newMessages) {
        this.messages = newMessages;
        this.currentMessageIndex = 0;
    }
}

// Initialiser le chat quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si on est sur une page où le chat doit apparaître
    const currentPage = window.location.pathname;
    
    let messages = [
        "Bienvenue sur Dek.Dek ! 👋",
        "Découvrez nos livres inspirants ! 📚",
        "Explorez nos citations motivantes ! 💭",
        "Bonne lecture ! ✨",
        "Merci de votre visite ! 😊"
    ];

    // Personnaliser les messages selon la page
    if (currentPage.includes('/livres')) {
        messages = [
            "Bienvenue dans notre librairie ! 📚",
            "Trouvez le livre parfait pour vous ! ✨",
            "Développement personnel et motivation ! 💪",
            "Cliquez sur moi pour plus de conseils ! 😊"
        ];
    } else if (currentPage.includes('/citations')) {
        messages = [
            "Inspirez-vous avec nos citations ! 💭",
            "Sagesse et motivation au quotidien ! ⭐",
            "Partagez vos citations préférées ! 💝",
            "Cliquez pour découvrir plus ! 😊"
        ];
    } else if (currentPage.includes('/admin')) {
        // Pas de chat sur les pages d'administration
        return;
    }

    // Créer et initialiser le chat
    window.pixelCat = new PixelCat();
    window.pixelCat.setMessages(messages);
});

// Fonction globale pour interagir avec le chat
window.triggerCatMessage = function(message) {
    if (window.pixelCat) {
        window.pixelCat.showMessage(message);
    }
};

