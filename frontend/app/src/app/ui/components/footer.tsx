"use client";

import { useTranslation } from "react-i18next";

const Footer = () => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };
    return (
      <footer className="text-white py-4 mt-10 bg-dark-900">
        <div className="container mx-auto text-center flex justify-center items-center flex-wrap gap-2">
          <p>&copy; 2025 Hypertube.</p>
          <p>
            {t("footer.madeBy")}{" "}
            <a
              href="https://github.com/johnconh"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-white"
            >
              jdasilva
            </a>{" "}
            {t("footer.and")}{" "}
            <a
              href="https://github.com/tentaclepurple"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-white"
            >
              imontero
            </a>
          </p>
          <button onClick={() => changeLanguage("en")}>🇬🇧</button>
          <button onClick={() => changeLanguage("es")}>🇪🇸</button>
        </div>
      </footer>
    );
  };
  
  export default Footer;
  