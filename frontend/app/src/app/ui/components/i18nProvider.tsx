"use client";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import "../../lib/i18n"; 

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const { i18n } = useTranslation();

  useEffect(() => {
    const savedLanguage = localStorage.getItem('i18nextLng');
    if (savedLanguage && ['en', 'es'].includes(savedLanguage)) {
      i18n.changeLanguage(savedLanguage);
    }
  }, [i18n]);

  return <>{children}</>;
}