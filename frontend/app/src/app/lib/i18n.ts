import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

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

i18n
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    
    interpolation: {
      escapeValue: false,
    },
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });

export default i18n;