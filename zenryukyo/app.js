
(() => {
  const galleryElement = document.getElementById('gallery');
  const template = document.getElementById('gallery-item-template');
  const lightbox = document.getElementById('lightbox');
  const lightboxImage = document.getElementById('lightbox-image');
  const lightboxCaption = document.getElementById('lightbox-caption');
  const closeButton = lightbox.querySelector('[data-lightbox-close]');
  const prevButton = lightbox.querySelector('[data-lightbox-prev]');
  const nextButton = lightbox.querySelector('[data-lightbox-next]');
  const overlay = lightbox.querySelector('[data-lightbox-overlay]');

  const focusControls = [closeButton, prevButton, nextButton];

  const state = {
    items: [],
    currentIndex: 0,
    previouslyFocused: null,
  };

  const fmtCaption = (item) => {
    if (!item || typeof item !== 'object') {
      return '蜀咏悄';
    }
    if (item.caption) return item.caption;
    if (item.alt) return item.alt;
    const base = item.src ? String(item.src).split('/').pop() : '';
    return base ? base.replace(/_/g, ' ').replace(/\.[^.]+$/, '') : '蜀咏悄';
  };

  const applyLightboxSizing = (item) => {
    if (item && item.w && item.h) {
      lightboxImage.width = item.w;
      lightboxImage.height = item.h;
      if ('aspectRatio' in lightboxImage.style) {
        lightboxImage.style.aspectRatio = `${item.w} / ${item.h}`;
      }
    } else {
      lightboxImage.removeAttribute('width');
      lightboxImage.removeAttribute('height');
      lightboxImage.style.removeProperty('aspect-ratio');
    }
  };

  const resetLightboxMedia = () => {
    lightboxImage.src = '';
    lightboxImage.removeAttribute('width');
    lightboxImage.removeAttribute('height');
    lightboxImage.style.removeProperty('aspect-ratio');
    lightboxCaption.textContent = '';
  };

  const setLightboxVisibility = (isOpen) => {
    lightbox.classList.toggle('is-open', isOpen);
    lightbox.setAttribute('aria-hidden', String(!isOpen));
    document.body.classList.toggle('is-lightbox-open', isOpen);
  };

  const updateLightbox = (index) => {
    const item = state.items[index];
    if (!item) return;
    state.currentIndex = index;
    lightboxImage.src = item.src;
    lightboxImage.alt = item.alt || fmtCaption(item);
    applyLightboxSizing(item);
    lightboxCaption.textContent = fmtCaption(item);
    const multipleItems = state.items.length > 1;
    prevButton.disabled = !multipleItems;
    nextButton.disabled = !multipleItems;
  };

  const cycleIndex = (delta) => {
    const total = state.items.length;
    if (!total) return state.currentIndex;
    return (state.currentIndex + delta + total) % total;
  };

  const handleKeydown = (event) => {
    if (lightbox.getAttribute('aria-hidden') === 'true') return;
    switch (event.key) {
      case 'Escape':
        event.preventDefault();
        closeLightbox();
        break;
      case 'ArrowLeft':
        event.preventDefault();
        updateLightbox(cycleIndex(-1));
        break;
      case 'ArrowRight':
        event.preventDefault();
        updateLightbox(cycleIndex(1));
        break;
      case 'Tab': {
        const focusableElements = focusControls.filter(
          (btn) => btn && !btn.disabled && btn.offsetParent !== null,
        );
        if (!focusableElements.length) {
          event.preventDefault();
          break;
        }
        const direction = event.shiftKey ? -1 : 1;
        const currentIndex = focusableElements.indexOf(document.activeElement);
        let nextIndex = currentIndex + direction;
        if (currentIndex === -1) {
          nextIndex = direction === 1 ? 0 : focusableElements.length - 1;
        } else {
          if (nextIndex < 0) nextIndex = focusableElements.length - 1;
          if (nextIndex >= focusableElements.length) nextIndex = 0;
        }
        event.preventDefault();
        focusableElements[nextIndex].focus();
        break;
      }
      default:
        break;
    }
  };

  const openLightbox = (index) => {
    if (!state.items.length) return;
    state.previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    updateLightbox(index);
    setLightboxVisibility(true);
    closeButton.focus();
    document.addEventListener('keydown', handleKeydown);
  };

  const closeLightbox = () => {
    setLightboxVisibility(false);
    resetLightboxMedia();
    document.removeEventListener('keydown', handleKeydown);
    if (state.previouslyFocused && document.contains(state.previouslyFocused)) {
      state.previouslyFocused.focus();
    }
  };

  const bindGalleryButtons = () => {
    const buttons = galleryElement.querySelectorAll('.gallery-item__button');
    buttons.forEach((button, domIndex) => {
      if (!(button instanceof HTMLButtonElement)) return;
      if (button.dataset.lightboxReady === 'true') return;
      const storedIndex = Number.parseInt(button.dataset.galleryIndex || '', 10);
      const itemIndex = Number.isNaN(storedIndex) ? domIndex : storedIndex;
      button.dataset.galleryIndex = String(itemIndex);
      const item = state.items[itemIndex];
      const caption = fmtCaption(item);
      if (!button.hasAttribute('aria-label')) {
        button.setAttribute('aria-label', `${caption}繧呈僑螟ｧ陦ｨ遉ｺ`);
      }
      button.addEventListener('click', () => openLightbox(itemIndex));
      button.dataset.lightboxReady = 'true';
    });
  };

  const renderGallery = () => {
    galleryElement.textContent = '';
    if (!Array.isArray(state.items) || !state.items.length) {
      const message = document.createElement('p');
      message.className = 'gallery-empty';
      message.textContent = '表示できる写真がありません。';
      galleryElement.appendChild(message);
      return;
    }
    const fragment = document.createDocumentFragment();
    state.items.forEach((item, index) => {
      const clone = template.content.cloneNode(true);
      const button = clone.querySelector('.gallery-item__button');
      const img = clone.querySelector('.gallery-item__image');
      const caption = clone.querySelector('.gallery-item__caption');
      if (!(button instanceof HTMLButtonElement) || !(img instanceof HTMLImageElement) || !(caption instanceof HTMLElement)) {
        return;
      }
      const thumbSrc = item.thumb || item.src;
      img.src = thumbSrc;
      img.alt = item.alt || fmtCaption(item);
      if (item.thumbWidth && item.thumbHeight) {
        img.width = item.thumbWidth;
        img.height = item.thumbHeight;
      } else if (item.w && item.h) {
        img.width = item.w;
        img.height = item.h;
      } else {
        img.removeAttribute('width');
        img.removeAttribute('height');
      }
      caption.textContent = fmtCaption(item);
      button.dataset.galleryIndex = String(index);
      button.setAttribute('aria-label', `${fmtCaption(item)}繧呈僑螟ｧ陦ｨ遉ｺ`);
      fragment.appendChild(clone);
    });
    galleryElement.appendChild(fragment);
    bindGalleryButtons();
  };

  const renderError = (message) => {
    galleryElement.textContent = '';
    const errorBox = document.createElement('div');
    errorBox.className = 'gallery-error';
    errorBox.setAttribute('role', 'alert');
    errorBox.textContent = message;
    galleryElement.appendChild(errorBox);
  };

  const parseInlineData = () => {
    const dataScript = document.getElementById('gallery-data');
    if (!dataScript) return null;
    const raw = dataScript.textContent.trim();
    if (!raw) return [];
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.error('ギャラリーデータの解析に失敗しました。', error);
      return null;
    }
  };

  const fetchGallery = async () => {
    try {
      const response = await fetch('photos/gallery.json', { cache: 'no-cache' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      state.items = Array.isArray(data) ? data : [];
      renderGallery();
    } catch (error) {
      console.error('ギャラリーデータの取得に失敗しました。', error);
      renderError('写真データの読み込みに失敗しました。ページを再読み込みしてください。');
    }
  };

  closeButton.addEventListener('click', closeLightbox);
  prevButton.addEventListener('click', () => updateLightbox(cycleIndex(-1)));
  nextButton.addEventListener('click', () => updateLightbox(cycleIndex(1)));
  overlay.addEventListener('click', closeLightbox);

  document.addEventListener('DOMContentLoaded', () => {
    const inlineItems = parseInlineData();
    if (inlineItems !== null) {
      state.items = inlineItems;
      if (inlineItems.length) {
        if (galleryElement.querySelector('.gallery-item')) {
          bindGalleryButtons();
        } else {
          renderGallery();
        }
      } else {
        renderGallery();
      }
      return;
    }
    fetchGallery();
  });
})();
