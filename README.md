# Strapi 3 to Strapi 4 Migration Script
This script migrates data from a Strapi 3 instance to a Strapi 4 instance, including handling relationships, media, and components.

---

## Features
- **Authentication**: Logs in to Strapi 3 using email and password, and uses an API key for Strapi 4.
- **Data Migration**: Fetches entries from a specified model in Strapi 3 and recreates them in Strapi 4.
- **Media Uploads**: Downloads media files from Strapi 3 and uploads them to Strapi 4, linking them to the correct entries.
- **Relationship Mapping**: Maps relationships between entries and updates them for Strapi 4.
- **Component Handling**: Processes nested components, including media and relationships within components.

---

## Prerequisites
1. **Python Version**:
   - Ensure Python 3.7 or higher is installed.
   - Install dependencies using `pip`:
     ```bash
     pip install -r requirements.txt
     ```
2. **Environment Configuration**:
   - Set up a `.env` file with your Strapi configuration. Use the `example.env` provided.

---

## Configuration
The script uses environment variables for sensitive information. Create a `.env` file based on the `example.env` template.

---

## Usage
1. **Set Up Environment**:
   - Place the `.env` file in the root directory of the project.

2. **Install Dependencies**:
   - The project uses `pip freeze` for dependency management. Use the provided `requirements.txt`:
     ```bash
     pip install -r requirements.txt
     ```
3. **Run the Script**:
    ```
    python migrate.py
    ```
4. **Monitor Logs**:
    The script outputs success or failure messages for each entry.

---

## Notes 
- Ensure that models in Strapi 4 match the structure of Strapi 3 models.
- Use the old_id field in Strapi 4 to map relationships.
- If you encounter media or relationship issues, review the Strapi 4 API documentation.

---

## Contributing
If you’d like to contribute to this project, feel free to submit a pull request or open an issue for discussion.

---

## License
This project is licensed under the MIT License.