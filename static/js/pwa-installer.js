// Script d'installation PWA pour KOASA
let deferredPrompt;
let installButton;

// Enregistrement du Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/service-worker.js')
      .then(registration => {
        console.log('✅ Service Worker enregistré:', registration.scope);
        
        // Vérifier les mises à jour toutes les heures
        setInterval(() => {
          registration.update();
        }, 3600000);
      })
      .catch(error => {
        console.error('❌ Erreur Service Worker:', error);
      });
  });
}

// Créer le bouton d'installation
function createInstallButton() {
  const button = document.createElement('button');
  button.id = 'pwaInstallBtn';
  button.className = 'btn btn-danger position-fixed bottom-0 end-0 m-3 shadow-lg';
  button.style.cssText = 'z-index: 9999; display: none; border-radius: 50px; padding: 12px 24px;';
  button.innerHTML = '<i class="fas fa-download me-2"></i>Installer l\'app';
  document.body.appendChild(button);
  return button;
}

// Afficher le bouton d'installation
window.addEventListener('DOMContentLoaded', () => {
  installButton = createInstallButton();
});

// Écouter l'événement beforeinstallprompt
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('💡 Prompt d\'installation disponible');
  
  // Empêcher l'affichage automatique
  e.preventDefault();
  
  // Sauvegarder l'événement
  deferredPrompt = e;
  
  // Afficher le bouton d'installation
  if (installButton) {
    installButton.style.display = 'block';
    
    // Animation d'entrée
    installButton.style.animation = 'slideInUp 0.5s ease-out';
  }
});

// Gérer le clic sur le bouton d'installation
document.addEventListener('click', async (e) => {
  if (e.target.id === 'pwaInstallBtn' || e.target.closest('#pwaInstallBtn')) {
    if (!deferredPrompt) {
      console.log('❌ Prompt d\'installation non disponible');
      return;
    }
    
    // Afficher le prompt d'installation
    deferredPrompt.prompt();
    
    // Attendre le choix de l'utilisateur
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`👤 Choix utilisateur: ${outcome}`);
    
    if (outcome === 'accepted') {
      console.log('✅ PWA installée avec succès');
      
      // Afficher une notification de succès
      showInstallSuccess();
    } else {
      console.log('❌ Installation refusée');
    }
    
    // Réinitialiser la variable
    deferredPrompt = null;
    
    // Masquer le bouton
    if (installButton) {
      installButton.style.display = 'none';
    }
  }
});

// Détecter si l'app est déjà installée
window.addEventListener('appinstalled', () => {
  console.log('✅ KOASA PWA installée avec succès!');
  
  // Masquer le bouton
  if (installButton) {
    installButton.style.display = 'none';
  }
  
  // Afficher notification
  showInstallSuccess();
  
  // Réinitialiser
  deferredPrompt = null;
});

// Fonction pour afficher le succès de l'installation
function showInstallSuccess() {
  const alert = document.createElement('div');
  alert.className = 'alert alert-success position-fixed top-0 start-50 translate-middle-x mt-3 shadow-lg';
  alert.style.cssText = 'z-index: 10000; min-width: 300px; animation: slideInDown 0.5s ease-out;';
  alert.innerHTML = `
    <div class="d-flex align-items-center">
      <i class="fas fa-check-circle me-2 fs-4"></i>
      <div>
        <strong>Application installée!</strong>
        <p class="mb-0 small">KOASA est maintenant sur votre écran d'accueil</p>
      </div>
      <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
  `;
  
  document.body.appendChild(alert);
  
  // Retirer automatiquement après 5 secondes
  setTimeout(() => {
    if (alert.parentElement) {
      alert.remove();
    }
  }, 5000);
}

// Détecter si l'app est lancée en mode standalone (installée)
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
  console.log('✅ App lancée en mode installé');
  
  // Ajouter une classe au body pour personnaliser le style si nécessaire
  document.body.classList.add('pwa-installed');
  
  // Masquer le bouton d'installation si visible
  if (installButton) {
    installButton.style.display = 'none';
  }
}

// Styles CSS pour les animations (à ajouter dynamiquement)
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInUp {
    from {
      opacity: 0;
      transform: translateY(100px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes slideInDown {
    from {
      opacity: 0;
      transform: translate(-50%, -100px);
    }
    to {
      opacity: 1;
      transform: translate(-50%, 0);
    }
  }
  
  #pwaInstallBtn:hover {
    transform: scale(1.05);
    transition: transform 0.2s ease;
  }
`;
document.head.appendChild(style);