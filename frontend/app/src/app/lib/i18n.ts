// frontend/app/src/app/lib/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslations from '../../../public/locales/en/translation.json';
import esTranslations from '../../../public/locales/es/translation.json';

const resources = {
  en: {
    translation: enTranslations,
  },
  es: {
    translation: esTranslations,
  },
};

// ✅ Leer localStorage antes de inicializar
const getInitialLanguage = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('i18nextLng');
    if (saved) return saved;  // Si hay guardado, usarlo
  }
  return 'en';  // Si no, inglés por defecto
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: getInitialLanguage(),  // ✅ Usa localStorage o 'en'
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
  });

export default i18n;