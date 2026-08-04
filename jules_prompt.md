Please create 4 new custom RenderCV templates in the `users/krushna/templates/` directory.

The templates should be designed as follows:
1. `modern-blue`: A sleek two-column layout with a light blue (#b0c4de) left sidebar (30% width) containing Contact Info, Profiles, and Skills. The right side is white with Summary, Experience, and Education. Use Roboto font.
2. `sleek-tech`: A minimalistic tech-focused single-column layout using the Fira Code font, with dark grey section headers and very compact spacing.
3. `two-column-dark`: A two-column layout where the left sidebar is dark (#1E1E1E) with white text, containing Contact Info, Profiles, and Skills. Right side is white with dark text. Use Inter font.
4. `creative`: A highly stylized single-column layout using a serif font (e.g., Merriweather) for headers, with a prominent centered name and contact info at the top, and subtle red accents for dates.

For each template:
- Create the folder (e.g. `users/krushna/templates/modern-blue/`)
- Include the necessary `.j2.tex` files (like `Header.j2.tex`, `Experience.j2.tex`, `Education.j2.tex`, etc.) that perfectly parse the RenderCV YAML schema.
