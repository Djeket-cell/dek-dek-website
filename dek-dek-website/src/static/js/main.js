// Dek.Dek Website JavaScript

// Configuration Wave
const WAVE_PAYMENT_URL = 'https://pay.wave.com/m/M_ci_v2lk7iNUKi75/c/ci/';

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    initializeWebsite();
});

function initializeWebsite() {
    // Initialize smooth scrolling
    initSmoothScrolling();
    
    // Initialize mobile menu if needed
    initMobileMenu();
    
    // Load books data
    loadBooks();
    
    // Load quotes data
    loadQuotes();
}

// Smooth scrolling for navigation links
function initSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Mobile menu functionality
function initMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
}

// Load books from API or data
async function loadBooks() {
    try {
        // For now, we'll use static data
        // In a real implementation, this would fetch from /api/books
        const books = [
            {
                id: 1,
                title: "Les Secrets du Développement Personnel",
                author: "Dek.Dek",
                description: "Un guide complet pour transformer votre vie et atteindre vos objectifs. Découvrez les techniques éprouvées pour développer votre potentiel et réussir dans tous les domaines de votre vie.",
                price: 5000,
                currency: "XOF",
                category: "Développement Personnel",
                pages: 120,
                format: "PDF"
            },
            {
                id: 2,
                title: "L'Art de la Communication Efficace",
                author: "Dek.Dek",
                description: "Maîtrisez l'art de la communication pour améliorer vos relations personnelles et professionnelles. Apprenez les techniques de persuasion et d'influence positive.",
                price: 4500,
                currency: "XOF",
                category: "Communication",
                pages: 95,
                format: "PDF"
            },
            {
                id: 3,
                title: "Entrepreneuriat et Innovation",
                author: "Dek.Dek",
                description: "Un manuel pratique pour les entrepreneurs en herbe. Découvrez comment créer, développer et faire prospérer votre entreprise dans l'économie moderne.",
                price: 6000,
                currency: "XOF",
                category: "Entrepreneuriat",
                pages: 150,
                format: "PDF"
            }
        ];
        
        displayBooks(books);
    } catch (error) {
        console.error('Erreur lors du chargement des livres:', error);
    }
}

// Display books in the grid
function displayBooks(books) {
    const booksContainer = document.getElementById('books-container');
    if (!booksContainer) return;
    
    booksContainer.innerHTML = '';
    
    books.forEach(book => {
        const bookCard = createBookCard(book);
        booksContainer.appendChild(bookCard);
    });
}

// Create a book card element
function createBookCard(book) {
    const card = document.createElement('div');
    card.className = 'book-card';
    
    card.innerHTML = `
        <div class="book-cover">
            📚
        </div>
        <div class="book-info">
            <h3 class="book-title">${book.title}</h3>
            <p class="book-author">par ${book.author}</p>
            <p class="book-description">${book.description}</p>
            <div class="book-meta">
                <span>${book.pages} pages</span>
                <span>${book.format}</span>
                <span>${book.category}</span>
            </div>
            <div class="book-price">${formatPrice(book.price, book.currency)}</div>
            <button class="btn btn-primary" onclick="purchaseBook(${book.id}, '${book.title}', ${book.price})">
                Acheter maintenant
            </button>
        </div>
    `;
    
    return card;
}

// Load quotes from API or data
async function loadQuotes() {
    try {
        const quotes = [
            {
                id: 1,
                text: "Le succès n'est pas final, l'échec n'est pas fatal : c'est le courage de continuer qui compte.",
                author: "Winston Churchill",
                category: "Motivation"
            },
            {
                id: 2,
                text: "La seule façon de faire du bon travail est d'aimer ce que vous faites.",
                author: "Steve Jobs",
                category: "Travail"
            },
            {
                id: 3,
                text: "L'éducation est l'arme la plus puissante qu'on puisse utiliser pour changer le monde.",
                author: "Nelson Mandela",
                category: "Éducation"
            },
            {
                id: 4,
                text: "Il n'y a qu'une façon d'éviter la critique : ne rien faire, ne rien dire et n'être rien.",
                author: "Aristote",
                category: "Courage"
            },
            {
                id: 5,
                text: "Le futur appartient à ceux qui croient en la beauté de leurs rêves.",
                author: "Eleanor Roosevelt",
                category: "Rêves"
            }
        ];
        
        displayQuotes(quotes);
    } catch (error) {
        console.error('Erreur lors du chargement des citations:', error);
    }
}

// Display quotes
function displayQuotes(quotes) {
    const quotesContainer = document.getElementById('quotes-container');
    if (!quotesContainer) return;
    
    quotesContainer.innerHTML = '';
    
    quotes.forEach(quote => {
        const quoteCard = createQuoteCard(quote);
        quotesContainer.appendChild(quoteCard);
    });
}

// Create a quote card element
function createQuoteCard(quote) {
    const card = document.createElement('div');
    card.className = 'quote-card';
    
    card.innerHTML = `
        <p class="quote-text">"${quote.text}"</p>
        <p class="quote-author">${quote.author}</p>
    `;
    
    return card;
}

// Format price with currency
function formatPrice(price, currency) {
    return `${price.toLocaleString()} ${currency}`;
}

// Handle book purchase
function purchaseBook(bookId, bookTitle, price) {
    // Show confirmation dialog
    const confirmed = confirm(`Vous allez acheter "${bookTitle}" pour ${formatPrice(price, 'XOF')}. Vous serez redirigé vers Wave pour le paiement. Continuer ?`);
    
    if (confirmed) {
        // Create payment instructions
        const instructions = `
Livre: ${bookTitle}
Prix: ${formatPrice(price, 'XOF')}

Instructions de paiement:
1. Vous allez être redirigé vers Wave
2. Payez exactement ${formatPrice(price, 'XOF')}
3. Prenez une capture d'écran de la confirmation
4. Envoyez la preuve de paiement à notre WhatsApp: +225 01 42 11 61 72
5. Vous recevrez le lien de téléchargement par email dans les 24h

Merci de votre confiance !
        `;
        
        alert(instructions);
        
        // Redirect to Wave payment
        window.open(WAVE_PAYMENT_URL, '_blank');
        
        // Track purchase attempt (for analytics)
        trackPurchaseAttempt(bookId, bookTitle, price);
    }
}

// Track purchase attempt for analytics
function trackPurchaseAttempt(bookId, bookTitle, price) {
    // This would typically send data to an analytics service
    console.log('Purchase attempt:', {
        bookId,
        bookTitle,
        price,
        timestamp: new Date().toISOString()
    });
}

// Contact form handling (if needed)
function handleContactForm(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    
    // Here you would typically send the data to your backend
    console.log('Contact form data:', data);
    
    alert('Merci pour votre message ! Nous vous répondrons dans les plus brefs délais.');
    event.target.reset();
}

// Utility functions
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add scroll-to-top button functionality
window.addEventListener('scroll', function() {
    const scrollButton = document.getElementById('scroll-to-top');
    if (scrollButton) {
        if (window.pageYOffset > 300) {
            scrollButton.style.display = 'block';
        } else {
            scrollButton.style.display = 'none';
        }
    }
});

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWebsite);
} else {
    initializeWebsite();
}

