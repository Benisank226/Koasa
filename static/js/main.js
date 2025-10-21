// ============================================================================
// KOASA - Script Principal
// ============================================================================

// Gestion du panier (stockage en mémoire)
let cart = [];

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadCart();
    updateCartBadge();
    initProductCards();
    initCartPage();
    initScrollAnimations();
    initProductDetails();
});

// ============================================================================
// GESTION DU PANIER
// ============================================================================

function loadCart() {
    const savedCart = sessionStorage.getItem('koasa_cart');
    if (savedCart) {
        try {
            cart = JSON.parse(savedCart);
        } catch (e) {
            cart = [];
        }
    }
}

function saveCart() {
    sessionStorage.setItem('koasa_cart', JSON.stringify(cart));
    updateCartBadge();
}

function addToCart(productId, productName, price, unit) {
    // Vérifier si le produit est disponible
    const productCard = document.querySelector(`[data-product-id="${productId}"]`);
    if (productCard && productCard.disabled) {
        showToast('❌ Ce produit est temporairement indisponible', 'warning');
        return;
    }

    const existingItem = cart.find(item => item.product_id === productId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            product_id: productId,
            name: productName,
            price: price,
            unit: unit,
            quantity: 1
        });
    }
    
    saveCart();
    showToast('✅ Produit ajouté au panier', 'success');
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.product_id !== productId);
    saveCart();
    
    if (typeof renderCart === 'function') {
        renderCart();
    }
}

function updateQuantity(productId, newQuantity) {
    const item = cart.find(item => item.product_id === productId);
    
    if (item) {
        if (newQuantity <= 0) {
            removeFromCart(productId);
        } else {
            item.quantity = parseFloat(newQuantity);
            saveCart();
        }
    }
    
    if (typeof renderCart === 'function') {
        renderCart();
    }
}

function clearCart() {
    cart = [];
    saveCart();
    
    if (typeof renderCart === 'function') {
        renderCart();
    }
}

function getCartTotal() {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

function getCartItemsCount() {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
}

function updateCartBadge() {
    const badge = document.getElementById('cartBadge');
    const badgeTop = document.getElementById('cartBadgeTop');
    
    const badges = [badge, badgeTop].filter(b => b !== null);
    const count = getCartItemsCount();
    
    badges.forEach(badge => {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    });
}

// ============================================================================
// INITIALISATION PAGES PRODUITS
// ============================================================================

function initProductCards() {
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    
    addToCartButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const productId = parseInt(this.dataset.productId);
            const productName = this.dataset.productName;
            const price = parseFloat(this.dataset.price);
            const unit = this.dataset.unit;
            
            addToCart(productId, productName, price, unit);
            
            // Animation du bouton
            this.innerHTML = '<i class="fas fa-check me-2"></i>Ajouté!';
            this.classList.add('btn-success');
            this.classList.remove('btn-danger');
            
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-cart-plus me-2"></i>Ajouter';
                this.classList.remove('btn-success');
                this.classList.add('btn-danger');
            }, 1500);
        });
    });
}

function initProductDetails() {
    // Les détails produits sont gérés dans les modals
    // Cette fonction est pour l'initialisation future
}

// ============================================================================
// PAGE PANIER
// ============================================================================

function initCartPage() {
    if (!document.getElementById('cartContainer')) return;
    
    renderCart();
    
    // Bouton vider panier
    const clearBtn = document.getElementById('clearCartBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            if (confirm('Voulez-vous vraiment vider votre panier ?')) {
                clearCart();
            }
        });
    }
    
    // Bouton commander via WhatsApp
    const whatsappBtn = document.getElementById('sendOrderWhatsAppBtn');
    if (whatsappBtn) {
        whatsappBtn.addEventListener('click', sendOrderByWhatsApp);
    }
}

function renderCart() {
    const container = document.getElementById('cartContainer');
    const totalElement = document.getElementById('cartTotal');
    const subtotalElement = document.getElementById('cartSubtotal');
    const emptyMessage = document.getElementById('emptyCartMessage');
    const cartActions = document.getElementById('cartActions');
    
    if (!container) return;
    
    if (cart.length === 0) {
        container.innerHTML = '';
        if (emptyMessage) emptyMessage.style.display = 'block';
        if (cartActions) cartActions.style.display = 'none';
        if (totalElement) totalElement.textContent = '0';
        if (subtotalElement) subtotalElement.textContent = '0';
        return;
    }
    
    if (emptyMessage) emptyMessage.style.display = 'none';
    if (cartActions) cartActions.style.display = 'block';
    
    container.innerHTML = cart.map(item => {
        const subtotal = item.price * item.quantity;
        return `
            <div class="card mb-3 shadow-sm cart-item animate-fade-in">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <h5 class="mb-1">${item.name}</h5>
                            <small class="text-muted">${item.price.toLocaleString('fr-FR')} FCFA / ${item.unit}</small>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small">Quantité</label>
                            <div class="input-group input-group-sm">
                                <button class="btn btn-outline-danger" onclick="updateQuantity(${item.product_id}, ${item.quantity - 0.5})">
                                    <i class="fas fa-minus"></i>
                                </button>
                                <input type="number" class="form-control text-center" 
                                       value="${item.quantity}" 
                                       min="0.5" step="0.5"
                                       onchange="updateQuantity(${item.product_id}, this.value)">
                                <button class="btn btn-outline-success" onclick="updateQuantity(${item.product_id}, ${item.quantity + 0.5})">
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <strong class="text-danger fs-5">${subtotal.toLocaleString('fr-FR')} FCFA</strong>
                        </div>
                        <div class="col-md-2 text-end">
                            <button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${item.product_id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    const total = getCartTotal();
    if (totalElement) {
        totalElement.textContent = total.toLocaleString('fr-FR') + ' FCFA';
    }
    if (subtotalElement) {
        subtotalElement.textContent = total.toLocaleString('fr-FR') + ' FCFA';
    }
}

// ============================================================================
// COMMANDES WHATSAPP - FONCTION CORRIGÉE
// ============================================================================

async function sendOrderByWhatsApp() {
    if (cart.length === 0) {
        showToast('❌ Votre panier est vide', 'warning');
        return;
    }
    
    const btn = document.getElementById('sendOrderWhatsAppBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Préparation...';
    
    try {
        // Calculer correctement le total
        const total = getCartTotal();
        
        // Récupérer l'adresse et les notes
        const deliveryAddress = document.getElementById('deliveryAddress')?.value || '';
        const notes = document.getElementById('orderNotes')?.value || '';
        
        // CORRECTION: Préparer les données du panier avec la structure attendue par le backend
        const cartItems = cart.map(item => ({
            product_id: item.product_id,  // Nom correct attendu par le backend
            name: item.name,              // Pour le message WhatsApp
            quantity: item.quantity,
            price: item.price,
            unit: item.unit
        }));
        
        console.log('📦 Données envoyées:', {  // Debug
            items: cartItems,
            total: total,
            delivery_address: deliveryAddress,
            notes: notes
        });
        
        const response = await fetch('/api/send-order-whatsapp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                items: cartItems,
                total: total,
                delivery_address: deliveryAddress,
                notes: notes
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            
            // VIDER LE PANIER après envoi réussi
            clearCart();
            renderCart();
            updateCartSummary();
            
            // Ouvrir WhatsApp dans un nouvel onglet
            if (data.whatsapp_url) {
                window.open(data.whatsapp_url, '_blank');
            }
            
            // Afficher l'ID de commande
            if (data.order_id) {
                showModal(
                    '✅ Commande créée!',
                    `Votre commande a été créée avec succès!<br><br>
                    <strong>ID de commande:</strong> ${data.order_id}<br><br>
                    WhatsApp s'ouvre automatiquement. Veuillez envoyer le message à l'admin.<br><br>
                    Vous pouvez suivre votre commande dans votre profil.`,
                    'success'
                );
            }
        } else {
            showToast('❌ ' + data.message, 'danger');
            console.error('❌ Erreur backend:', data); // Debug
        }
    } catch (error) {
        showToast('❌ Erreur: ' + error.message, 'danger');
        console.error('❌ Erreur fetch:', error); // Debug
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fab fa-whatsapp me-2"></i>Commander via WhatsApp';
    }
}

// ============================================================================
// UTILITAIRES UI
// ============================================================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed animate-slide-in`;
    toast.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 5000);
}

function showModal(title, message, type = 'info') {
    const iconMap = {
        success: 'fa-check-circle text-success',
        warning: 'fa-exclamation-triangle text-warning',
        danger: 'fa-times-circle text-danger',
        info: 'fa-info-circle text-info'
    };
    
    const icon = iconMap[type] || iconMap.info;
    
    const modalHtml = `
        <div class="modal fade" id="dynamicModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title">
                            <i class="fas ${icon} me-2"></i>${title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${message}
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Supprimer ancien modal si existe
    const oldModal = document.getElementById('dynamicModal');
    if (oldModal) oldModal.remove();
    
    // Ajouter nouveau modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('dynamicModal'));
    modal.show();
    
    // Nettoyer après fermeture
    document.getElementById('dynamicModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Animation au scroll
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.product-card, .card').forEach(el => {
        observer.observe(el);
    });
}

// Mise à jour du résumé du panier
function updateCartSummary() {
    const subtotal = getCartTotal();
    const subtotalElement = document.getElementById('cartSubtotal');
    const totalElement = document.getElementById('cartTotal');
    
    if (subtotalElement) {
        subtotalElement.textContent = subtotal.toLocaleString('fr-FR') + ' FCFA';
    }
    if (totalElement) {
        totalElement.textContent = subtotal.toLocaleString('fr-FR') + ' FCFA';
    }
}

// Surcharger la fonction renderCart pour inclure le résumé
const originalRenderCart = renderCart;
renderCart = function() {
    originalRenderCart();
    updateCartSummary();
};

// Mise à jour du badge du panier en haut
function updateCartBadgeTop() {
    const badge = document.getElementById('cartBadgeTop');
    if (badge) {
        const count = getCartItemsCount();
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

// ============================================================================
// GESTION DES PRODUITS (NOUVEAU)
// ============================================================================

// Afficher les détails d'un produit
function showProductDetails(product) {
    const content = document.getElementById('productDetailsContent');
    
    const statusBadge = product.is_available ? 
        '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Disponible</span>' :
        '<span class="badge bg-warning text-dark"><i class="fas fa-pause me-1"></i>Indisponible</span>';
    
    const categoryIcon = product.category_ref ? product.category_ref.icon : 'fas fa-cube';
    const categoryName = product.category_ref ? product.category_ref.name : 'Non catégorisé';
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                ${product.image_url ? `
                    <img src="${product.image_url}" class="img-fluid rounded" alt="${product.name}" style="max-height: 300px; object-fit: cover;">
                ` : `
                    <div class="bg-danger text-white d-flex align-items-center justify-content-center rounded" style="height: 200px;">
                        <i class="fas fa-drumstick-bite fa-4x opacity-25"></i>
                    </div>
                `}
            </div>
            <div class="col-md-6">
                <h4 class="text-danger">${product.name}</h4>
                <div class="mb-3">
                    ${statusBadge}
                    <span class="badge bg-secondary ms-2">
                        <i class="${categoryIcon} me-1"></i>${categoryName}
                    </span>
                </div>
                
                <p class="mb-3">${product.description || 'Viande fraîche de qualité'}</p>
                
                <table class="table table-sm">
                    <tr>
                        <th>Prix:</th>
                        <td><strong class="text-danger fs-5">${product.price.toLocaleString('fr-FR')} FCFA</strong></td>
                    </tr>
                    <tr>
                        <th>Unité:</th>
                        <td>${product.unit}</td>
                    </tr>
                    <tr>
                        <th>Stock:</th>
                        <td>
                            ${product.stock > 10 ? 
                                `<span class="badge bg-success">${product.stock} disponible(s)</span>` :
                                product.stock > 0 ?
                                `<span class="badge bg-warning text-dark">${product.stock} - Stock limité</span>` :
                                `<span class="badge bg-danger">Rupture de stock</span>`
                            }
                        </td>
                    </tr>
                    <tr>
                        <th>Catégorie:</th>
                        <td><i class="${categoryIcon} me-2"></i>${categoryName}</td>
                    </tr>
                </table>
                
                <div class="d-grid gap-2 mt-4">
                    ${product.is_available ? `
                        <button class="btn btn-danger btn-lg" onclick="addToCartFromModal(${product.id}, '${product.name.replace(/'/g, "\\'")}', ${product.price}, '${product.unit}')">
                            <i class="fas fa-cart-plus me-2"></i>Ajouter au panier
                        </button>
                    ` : `
                        <button class="btn btn-outline-secondary btn-lg" disabled>
                            <i class="fas fa-pause me-2"></i>Produit temporairement indisponible
                        </button>
                    `}
                    <button class="btn btn-outline-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times me-2"></i>Fermer
                    </button>
                </div>
            </div>
        </div>
    `;
    
    new bootstrap.Modal(document.getElementById('productDetailsModal')).show();
}

// Ajouter au panier depuis le modal
function addToCartFromModal(productId, productName, price, unit) {
    addToCart(productId, productName, price, unit);
    bootstrap.Modal.getInstance(document.getElementById('productDetailsModal')).hide();
}

// ============================================================================
// FONCTIONS GLOBALES
// ============================================================================

// Exposer les fonctions globalement pour les templates
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateQuantity = updateQuantity;
window.clearCart = clearCart;
window.getCartTotal = getCartTotal;
window.getCartItemsCount = getCartItemsCount;
window.renderCart = renderCart;
window.sendOrderByWhatsApp = sendOrderByWhatsApp;
window.showToast = showToast;
window.showModal = showModal;
window.showProductDetails = showProductDetails;
window.addToCartFromModal = addToCartFromModal;