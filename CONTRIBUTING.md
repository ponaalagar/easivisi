# Contributing to EasiVisi 🎯

First off, thank you for considering contributing to EasiVisi! It's people like you that make EasiVisi such a great tool for the Computer Vision community.

By contributing, you are helping democratize AI training and making it accessible to everyone.

---

## 📑 Table of Contents

1.  [How Can I Contribute?](#how-can-i-contribute)
2.  [Development Setup](#development-setup)
3.  [Styleguides](#styleguides)
4.  [Pull Request Process](#pull-request-process)
5.  [Reporting Bugs](#reporting-bugs)
6.  [Suggesting Enhancements](#suggesting-enhancements)

---

## 🚀 How Can I Contribute?

### Reporting Bugs
If you find a bug, please search the [GitHub Issues](https://github.com/ponaalagar/easivisi/issues) to see if it has already been reported. If not, open a new issue and include:
*   A clear, descriptive title.
*   Steps to reproduce the problem.
*   The environment details (OS, Python version, Browser).
*   Logs or screenshots if applicable.

### Suggesting Enhancements
We love new ideas! If you have a feature request:
*   Check if it's already on the [Roadmap](README.md#-roadmap).
*   Open an issue with the "enhancement" label.
*   Explain why this feature would be useful and how it should work.

### Code Contributions
Whether it's a small fix or a major feature:
1.  Fork the repo.
2.  Create a branch for your work.
3.  Submit a Pull Request.

---

## 🛠️ Development Setup

To set up EasiVisi locally for development:

1.  **Clone your fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/easivisi.git
    cd easivisi
    ```

2.  **Set up a Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # Also install Flask manually if missing from requirements
    pip install flask werkzeug
    ```

4.  **Run in Debug Mode:**
    ```bash
    python app.py
    ```
    The application will be available at `http://localhost:5000`. Changes to Python files will trigger an automatic reload.

---

## 🎨 Styleguides

### Python (Backend)
*   Follow **PEP 8** standards.
*   Use descriptive variable and function names.
*   Include docstrings for public functions and classes.
*   **Linting:** It is recommended to use `flake8` or `black` for formatting.

### Frontend (HTML/CSS/JS)
*   **CSS:** Use the existing design system tokens. Keep CSS in `static/css` or within `<style>` blocks if component-specific.
*   **JavaScript:** Use modern ES6+ syntax. Avoid heavy external libraries unless necessary.
*   **HTML:** Ensure semantic HTML and accessibility (ARIA labels).

### Git Commit Messages
*   Use the imperative mood ("Add feature" not "Added feature").
*   Keep the first line short (under 50 characters).
*   Reference issues and pull requests after the first line.
    *   *Example:* `feat: add undo/redo to annotation tool (#42)`

---

## 🔄 Pull Request Process

1.  **Update Documentation:** If your change affects how the tool is used, update the `README.md`.
2.  **Test your changes:** Ensure the training pipeline and web UI still function correctly.
3.  **Squash commits:** Keep your history clean by squashing minor fix-up commits.
4.  **Describe your PR:** Explain what you changed and why. Mention any related issues.
5.  **Review:** Wait for a maintainer to review your PR. Be open to feedback!

---

## 📄 License
By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

## 🙏 Credits
Special thanks to all contributors who help make **EasiVisi** better every day! 

[Back to top](#contributing-to-easivisi-)
