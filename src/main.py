from gitingest import ingest
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
# Load environment variables from .env file
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
summary, tree, content = ingest("code/kitchensink")
    
def analyze_java_code() -> str:
    prompt = f"""
    You are an expert Java developer specializing in Spring Boot and MongoDB migrations.
    
    Analyze the following Java code structure and provide a detailed migration plan to convert this exact given project to a Spring Boot application using MongoDB:
    Here `tree` is the directory structure of the Java code and `content` is the content of the Java files. You need to analyze the code and provide a detailed migration plan to migrate this same exact project in to Sprting boot app.
    
    Java code directory structure:
    {tree}

    Java Files:
    {content}
    
    ## Project: DB Migration Tool
    - I am building db migration tool in python programming language. I have given code reposiotory which was built in Java and runs on JBoss EAP application server and it has relational database.
    - This tool will analyze this code reposiotry and create nice readmd.md file with detailed steps on how to migrate this to Sptring Bott + mongo db.
    - Please find more detailed information below 

    ## Please keep in mind below steps when generating code for this tool
    - First analyze the given code and then using Open AI llm tool you need to generate readme.md file where you have to list down all the stpes on how to migrate this app under the folder tool to new stack using Sptring Bott + mongo db.
    - The target stack to modernise this application is the latest stable version of Spring Boot based on Java 21 working with MongoDB, moving away from the Relational database.


    ## The migration plan should include:
    1. Steps to set up a new Spring Boot project
    2. How to migrate the existing Java classes to Spring Boot components
    3. Changes required to switch from a relational database to MongoDB
    4. Any necessary configuration changes
    5. Suggestions for updating the build process
    6. Testing considerations
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "developer", "content": "You are an expert Java developer specializing in Spring Boot and MongoDB migrations."},
                {"role": "user", "content": prompt},
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")

def suggest_mongodb_schema() -> str:
    prompt = f"""
    You are an expert in Mongo DB database design, specialized in MongoDB schema design. You will help me to create details plan to migrate this relational database to mongo db document database. You should generate end output in readme.md file format.
    
    Analyze the following Java code structure and suggest a MongoDB schema based on the current relational database structure:
    Here `tree` is the directory structure of the Java code and `content` is the content of the Java files. You need to analyze the code and provide a detailed migration plan to migrate relation DB in to Mongo DB database.
    
    Java code directory structure:
    {tree}

    Java Files:
    {content}
    
    ## Project: DB Migration Tool
    - I am building db migration tool in python programming language. I have given code reposiotory which was built in Java and runs on JBoss EAP application server and it has relational database.
    - This tool will analyze this code reposiotry and create nice readmd.md file with detailed steps on how to migrate this to Sptring Bott + mongo db.
    - Please find more detailed information below 

    ## Please keep in mind below steps when generating code for this tool
    - First analyze the given code and then using Open AI llm tool you need to generate readme.md file where you have to list down all the stpes on how to migrate this app under the folder tool to new stack using Sptring Bott + mongo db.
    - The target stack to modernise this application is the latest stable version of Spring Boot based on Java 21 working with MongoDB, moving away from the Relational database.
    - Stretch goal: The tool can also suggest a schema for MongoDB based on the static code scan. It would be great.


    ## Provide a detailed MongoDB schema suggestion, including:
    1. Document structures
    2. Embedded documents vs. references
    3. Indexing recommendations
    4. Any necessary data transformations
    
    # Please provide a detailed MongoDB schema suggestion based on the current relational database structure. Make sure to include below steps in your mongodb schema migration plan.
    - MongoDB Migration Strategy must include below steps in detailed manner:
        - You must include JAVA files to change in order to migrate this to MongoDB
        - MongoDB Schema Design
        - Data Model
        - Indexing Strategy
        - Embedded vs. Referenced Documents
        - Configuration Changes
        - Create MongoDB initialization script
        - Detailed Implementation Steps
        - MongoDB Dependencies 
        - Testing Strategy
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "developer", "content": "You are an expert in database design, specializing in MongoDB schema design."},
                {"role": "user", "content": prompt},
            ]
        )

        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")

def main() -> None:
    """Main function to execute the script."""
    print("Hello, World!")
    # ingest_files()
    migration_plan = analyze_java_code()
    mongodb_schema = suggest_mongodb_schema()
    with open("Migration_Plan.md", "w") as f:
        f.write("# Migration Plan: Java to Spring Boot with MongoDB\n\n")
        f.write("## Project Analysis\n\n")
        f.write("## Migration Plan\n\n")
        f.write(migration_plan)
        f.write("\n\n## Suggested MongoDB Schema\n\n")
        f.write(mongodb_schema)

if __name__ == "__main__":
    main()
