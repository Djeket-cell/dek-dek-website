// Quotes page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadQuotes();
});

async function loadQuotes() {
    const quotesGrid = document.getElementById('quotes-grid');
    const loadingIndicator = document.getElementById('loading-quotes');
    
    try {
        const response = await fetch('/api/quotes');
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            displayQuotes(result.data);
        } else {
            quotesGrid.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666; grid-column: 1 / -1;">
                    <h3>Aucune citation disponible pour le moment</h3>
                    <p>Revenez bientôt pour découvrir nos citations inspirantes !</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erreur lors du chargement des citations:', error);
        quotesGrid.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #e74c3c; grid-column: 1 / -1;">
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les citations. Veuillez réessayer plus tard.</p>
            </div>
        `;
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function displayQuotes(quotes) {
    const quotesGrid = document.getElementById('quotes-grid');
    
    quotesGrid.innerHTML = quotes.map(quote => `
        <div class="quote-card">
            <div class="quote-text">"${quote.text}"</div>
            <div class="quote-author">— ${quote.author}</div>
            <div class="quote-category">${quote.category}</div>
        </div>
    `).join('');
}

