const Footer = () => {
    return (
      <footer className="text-white py-4 mt-10">
        <div className="container mx-auto text-center flex justify-center items-center">
          <p>&copy; 2025 Hypertube.</p>
          <p>
            Made by{" "}
            <a
              href="https://github.com/johnconh"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-white"
            >
              jdasilva
            </a>{" "}
            and{" "}
            <a
              href="https://github.com/tentaclepurple"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-white"
            >
              imontero
            </a>
          </p>
        </div>
      </footer>
    );
  };
  
  export default Footer;
  