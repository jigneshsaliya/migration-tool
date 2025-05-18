# Migration Plan: Java to Spring Boot with MongoDB

## Project Analysis

## Migration Plan

Certainly! Here is a detailed migration plan (in markdown format) for migrating the given **kitchensink** Java EE/Jakarta EE (JBoss EAP, JPA/H2, JSF, REST, CDI, Bean Validation) project to a modern **Spring Boot** application with **MongoDB** as database (running Java 21, with latest Spring Boot).

---

# Migration Plan: kitchensink Project to Spring Boot + MongoDB

## Table of Contents

1. [Set up a new Spring Boot project](#setup)
2. [Migrate Java classes to Spring Boot components](#migrate-components)
3. [Migrate from Relational DB to MongoDB](#migrate-db)
4. [Update configurations](#config)
5. [Build Process](#build)
6. [Testing Considerations](#test)
7. [Additional Notes](#notes)


---

<a name="setup"></a>
## 1. Set up a New Spring Boot Project

**a. Generate a new Spring Boot project skeleton:**

- Use [Spring Initializr](https://start.spring.io/) or your favorite IDE:
  - **Language:** Java
  - **Java Version:** 21
  - **Spring Boot Version:** Latest stable (e.g., 3.2.x)
  - **Packaging:** Jar (or War if JSF is needed, but recommended to move to pure REST and modern UI)
  - **Dependencies:**
    - Spring Web
    - Spring Data MongoDB
    - Spring Validation
    - Lombok (optional, for reduced boilerplate)
    - (Optionally, Spring Boot DevTools for development)
    - JUnit, Mockito for testing

**b. Folder structure:**

```
tool/
 ├── src/main/java/com/example/kitchensink/
 │    ├── controller/
 │    ├── model/
 │    ├── repository/
 │    ├── service/
 │    └── ... (others as needed)
 ├── src/test/java/com/example/kitchensink/
 │    └── ...
 ├── src/main/resources/
 │    ├── application.properties
 │    └── ...
 └── pom.xml
```

**c. Replace `org.jboss.as.quickstarts.kitchensink` package with `com.example.kitchensink`** (or appropriate).

---

<a name="migrate-components"></a>
## 2. Migrate Existing Java Classes to Spring Boot Components

Map the old Java EE constructs to Spring Boot concepts:

| Java EE Component | New Spring Boot Equivalent     |
|-------------------|-------------------------------|
| @Entity           | @Document (Spring Data Mongo) |
| @Stateless, CDI   | @Service/@Component etc.      |
| @Inject           | @Autowired/@Inject            |
| JPA Repository    | MongoRepository (Spring Data) |
| @RequestScoped    | Stateless beans (default)     |
| JSF Controllers   | @RestController or @Controller|
| JAX-RS @Path      | @RequestMapping/@GetMapping   |
| Bean Validation   | Spring's @Valid/@Validated    |

**Migration mapping for this project:**

### a. Model: `Member`

- Convert `@Entity` to `@Document(collection="members")`
- MongoDB uses `_id`, map it to existing `id` field.
- Bean validation annotations largely remain the same.
- Remove any JPA/Hibernate imports and use `org.springframework.data.annotation.Id` etc.

### b. Repository Layer

- Replace custom DAO/repository code with a Spring Data MongoDB interface:

    ```java
    public interface MemberRepository extends MongoRepository<Member, String> {
        Optional<Member> findByEmail(String email);
        List<Member> findAllByOrderByNameAsc();
    }
    ```
    - Use `String` or `ObjectId` as id type in MongoDB (adjust in model class).

### c. Service Layer

- `MemberRegistration`: Recreate as a Spring `@Service` class.
- Move persistence logic to use MongoRepository methods instead of JPA `EntityManager`.
- Fire events using Spring Application Events if needed (for list refresh, or just update the list after `.save()`).

### d. Controller Layer

- `MemberController` (JSF Managed Bean):  
  - If the UI is being rebuilt (as a SPA or using Thymeleaf), create corresponding REST endpoints and/or web controller methods.
  - For REST: Use `@RestController`. For each endpoint in the original JAX-RS resource, create an equivalent Spring method:

    ```java
    @RestController
    @RequestMapping("/api/members") // e.g. /api/members
    public class MemberRestController {
      // GET, POST etc. as per MemberResourceRESTService
    }
    ```

- For web interface:
  - Migrate to Thymeleaf or React/Vue SPA. If Thymeleaf: use `@Controller` and return `.html` templates.
  - If keeping JSF: Consider running it in a legacy/bridge mode, but preferred is to migrate to REST + modern JS UI.

### e. Bean Validation

- All validation annotations mostly stay the same.  
- Use `@Valid` on controller method parameters to enable validation.

### f. Logging

- Use `org.slf4j.Logger` with Spring's logging configuration.

---

<a name="migrate-db"></a>
## 3. Migrating from Relational Database (JPA/H2) to MongoDB

**a. Entities (`@Entity` → `@Document`)**
  - Replace all JPA annotations with corresponding Spring Data MongoDB ones.
  - Use `@Document(collection="members")`.
  - Change `@Id @GeneratedValue` to use `@Id` (Spring Data) and let MongoDB auto-create `_id`.

**b. Database constraints & migrations**
  - MongoDB does NOT enforce schema or unique constraints by default.
  - Programmatically check for uniqueness (e.g., for email), or define a unique index (see [Mongo Indexes](https://docs.mongodb.com/manual/indexes/)).
  - Remove all JPA-related configurations, SQL scripts, DDL files, and the `persistence.xml`.

**c. Repository Query Adjustments**
  - All JPA queries become simple repository methods (Spring Data MongoDB will auto-implement queries by method name).
  - Manual queries for sorting, or uniqueness checks, should be implemented as custom methods in the Spring Data repository.

**d. Seed Data**
  - Migrate `import.sql` to a CommandLineRunner bean or use MongoDB's data initialization features.
  - Example:  
    ```java
    @Component
    public class DataLoader implements CommandLineRunner {
      private final MemberRepository repo;
      public DataLoader(MemberRepository repo) { this.repo = repo; }
      public void run(String... args) {
        if (repo.count() == 0) {
          repo.save(new Member(...));
        }
      }
    }
    ```

---

<a name="config"></a>
## 4. Necessary Configuration Changes

**a. Remove JPA and datasource configuration files:**
  - Delete `persistence.xml`, `kitchensink-quickstart-ds.xml`, and related files.

**b. Add MongoDB configuration to `application.properties`:**

  ```properties
  # MongoDB connection
  spring.data.mongodb.uri=mongodb://localhost:27017/kitchensink
  spring.data.mongodb.database=kitchensink
  ```

  - Adjust host/db/credentials as appropriate.
  - Remove any references to JPA and Hibernate properties.
  - Set server port and context path if needed.

**c. Other Spring Boot Config:**

  - Set `server.port` and `server.servlet.context-path` if needed.
  - Configure `spring.jackson` options if customizing JSON format.

**d. Validation Messages:**
  - Place in `messages.properties` in `src/main/resources` if used.

---

<a name="build"></a>
## 5. Build Process

- Use **Maven** or **Gradle** (Maven generally easier for migration):
  - The pom.xml will reference Spring Boot and dependencies instead of old JBoss-centric BOMs.
- Use Spring Boot Maven Plugin for building and running:

  ```xml
  <plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-maven-plugin</artifactId>
    <version>3.2.x</version>
  </plugin>
  ```

- Typical build/run commands:
  ```
  mvn clean spring-boot:run
  mvn test
  ```

---

<a name="test"></a>
## 6. Testing Considerations

**a. Unit/integration tests:**  
- Use JUnit 5 (default in Spring Boot).
- Replace Arquillian with standard Spring Boot test infrastructure (`@SpringBootTest`, `@DataMongoTest`, `@WebMvcTest`, etc.).
- Mock MVC for REST endpoint testing.
- Use [embedded MongoDB](https://github.com/flapdoodle-oss/de.flapdoodle.embed.mongo) for integration tests.
- Migrate tests:
  - Unit tests are similar (change DI to Spring `@Autowired`).
  - Tests that deploy to JBoss EAP with Arquillian: Rewrite as `@SpringBootTest` or mock MVC tests.

**b. Remove all Arquillian and JBoss EAP test configs/files**.

---

<a name="notes"></a>
## 7. Additional Notes & Suggestions

- **Frontend:** Migrate JSF pages (`.xhtml`) to Thymeleaf templates, or separate Single Page Application (React/Vue/Angular), consuming your new REST endpoints.
- **CDI, EJB, JPA:** All are replaced by Spring's DI, Service, Repository abstractions, and MongoDB as the data source.
- **Events:** Use Spring's ApplicationEvents if you need to broadcast domain events.
- **Validation:** Spring Boot will handle bean validation and validation messages on REST endpoints natively.
- **Deployment:** Spring Boot apps are stand-alone jars (no need to deploy to JBoss/Wildfly); simply execute `java -jar <app>.jar`.
- **Dockerization:** Optionally, create Dockerfiles for both the Spring Boot app and MongoDB for easy cloud deployment.

---

## Example: Member Entity Before and After

**Before (JPA):**
```java
@Entity
@XmlRootElement
@Table(uniqueConstraints = @UniqueConstraint(columnNames = "email"))
public class Member implements Serializable {
    @Id @GeneratedValue private Long id;
    // ...
}
```

**After (Spring Data MongoDB):**
```java
@Document(collection = "members")
public class Member {
    @Id private String id; // OR private ObjectId id;
    // add @Indexed(unique=true) on email if needed
    // ...
}
```

---

## Example: Member REST Controller

```java
@RestController
@RequestMapping("/api/members")
public class MemberRestController {
    private final MemberRepository repo;
    // Constructor injection

    @GetMapping
    public List<Member> listAll() {
        return repo.findAllByOrderByNameAsc();
    }
    @GetMapping("/{id}")
    public ResponseEntity<Member> get(@PathVariable String id) {
        return repo.findById(id)
                   .map(ResponseEntity::ok)
                   .orElse(ResponseEntity.notFound().build());
    }
    @PostMapping
    public ResponseEntity<?> create(@RequestBody @Valid Member member, BindingResult result) {
        if (repo.findByEmail(member.getEmail()).isPresent()) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("email", "Email taken"));
        }
        var saved = repo.save(member);
        return ResponseEntity.ok(saved);
    }
}
```

---

# Final Steps & Checklist

- [ ] Generate new Spring Boot project skeleton.
- [ ] Migrate model, repository, and service classes.
- [ ] Migrate REST API endpoints, adjust to RESTful standards if possible.
- [ ] Migrate validation logic.
- [ ] Remove all JPA/EE/Hibernate artifacts and descriptors.
- [ ] Implement MongoDB repository and migration of data loading.
- [ ] Update properties to use MongoDB.
- [ ] Re-create tests using Spring Boot test features.
- [ ] Update or replace UI as appropriate.
- [ ] Build and run application using Spring Boot.

---

**You should now have a fully-functional Spring Boot + MongoDB application, with the business logic and API surface modernized for easier deployment and cloud-readiness.**

## Suggested MongoDB Schema

```markdown
# Migrating Kitchensink Application to Spring Boot & MongoDB

This document provides a **detailed plan, MongoDB schema design, and technical steps to migrate** the Kitchensink application (originally Java/Jakarta EE + RDBMS on JBoss EAP) to **Spring Boot (Java 21)** with **MongoDB** as the new database backend.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Java Artifacts to Change for MongoDB Migration](#1-key-java-artifacts-to-change)
3. [MongoDB Schema Design](#2-mongodb-schema-design)
   - [Document Structures (with Example JSON)](#document-structures)
   - [Embedded vs Referenced Documents](#embedded-vs-referenced-documents)
   - [Indexes and Indexing Recommendations](#indexing-recommendations)
   - [Data Transformation](#data-transformation)
4. [Spring Boot Integration Steps](#3-spring-boot-integration-steps)
5. [MongoDB Dependencies](#4-mongodb-dependencies)
6. [MongoDB Initialization Script](#5-mongodb-initialization-script)
7. [Testing Strategy](#6-testing-strategy)
8. [Summary Table: Old vs. New](#7-summary-table-old-vs-new)

---

## Overview

- **Original Stack**: Java EE (Jakarta EE) on JBoss, JSF, JPA/Hibernate (RDBMS), EJB, JAX-RS.
- **New Stack**: Spring Boot 3.x/Java 21, Spring Web, Spring Data MongoDB, REST controllers, no EJB/CDI, and MongoDB as backend.
- **Primary Domain Model**: `Member` entity with fields `id`, `name`, `email`, `phoneNumber`.

---

## 1. Key Java Artifacts to Change

### You will need to create or modify the following Java files:

| Old Layer                              | New Spring Boot Artifacts            | Main Change                                          |
|---------------------------------------- |--------------------------------------|------------------------------------------------------|
| `Member.java` (JPA Entity)              | `Member.java` (Spring's @Document)   | Use Spring Data/Mongo annotations                    |
| `MemberRepository.java` (JPA repo)      | `MemberRepository.java` (Mongo repo) | Extend `MongoRepository`; update queries             |
| `MemberRegistration.java` (EJB)         | `MemberService.java`                 | Service class, remove EJB, use Spring @Service       |
| `MemberController.java`, REST endpoints | `MemberRestController.java`          | Spring @RestController replaces JAX-RS endpoints     |
| JPA configuration, persistence.xml      | Spring application.yml/properties    | Mongo properties, remove JPA                         |
| Test classes (Arquillian, etc.)         | JUnit/SpringBootTest                 | Use embedded Mongo for integration testing           |

---

## 2. MongoDB Schema Design

### Document Structures

**Original Relational Table (Member):**

| id (PK) | name  | email (unique)         | phone_number  |
|---------|-------|------------------------|---------------|
| 0       | John Smith | john.smith@mailinator.com | 2125551212  |
| ...     | ...   | ...                    | ...           |

#### MongoDB Document (`members` collection)

```json
{
  "_id": ObjectId("..."),
  "name": "John Smith",
  "email": "john.smith@mailinator.com",
  "phoneNumber": "2125551212"
}
```

- `id` : Use MongoDB’s automatic `_id` (`ObjectId`), or map to a Long/int if you need migration compatibility.
- `name`, `email`, `phoneNumber` : Same fields.
- **Note:** Unique constraint on `email`.

**No other relational entities or relationships exist, so a straightforward mapping is possible.**

#### Example: `Member.java` (Spring Style)

```java
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import jakarta.validation.constraints.*;

@Document(collection = "members")
public class Member {
    @Id
    private String id; // usually String for MongoDB's ObjectId

    @NotNull
    @Size(min = 1, max = 25)
    @Pattern(regexp = "[^0-9]*", message = "Must not contain numbers")
    private String name;

    @NotNull
    @Email
    private String email;

    @NotNull
    @Size(min = 10, max = 12)
    @Pattern(regexp = "\\d{10,12}") // or use @Digits, but for strings use regex
    private String phoneNumber;

    // getters/setters
}
```

---

### Embedded vs. Referenced Documents

- There are **no other tables** or relationships in the given code. Thus, **no need for embedding or referencing other documents**.
- If future features require member sub-collections (e.g. addresses, orders), consider embedding small, tightly-linked collections; otherwise, use references.

---

### Indexing Recommendations

- Ensure **unique index** on `email` field.
- Add standard index on `name` **if you need to query frequently by name**.

**Example (MongoDB shell):**
```js
db.members.createIndex({ email: 1 }, { unique: true });
db.members.createIndex({ name: 1 });
```
For Spring Boot: You can use `@Indexed(unique=true)` on the `email` field.

---

### Data Transformation

- **Primary transformation**: Each row of the RDBMS table becomes a JSON document.
- Convert integer/long ids (if needed) to `ObjectId` string, or explicitly store external ids if required for compatibility.
- Validate unique constraints during data migration.
- Existing Bean Validation annotations can be retained (Spring Boot supports Jakarta Validation on incoming data).

---

## 3. Spring Boot Integration Steps

### a. Domain/Entity

- Move `Member.java` to `@Document` & use `@Id`.
- Update field annotations as shown above.

### b. Repository

**Old:**
```java
public class MemberRepository {
    // JPA's EntityManager
}
```

**New:**
```java
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MemberRepository extends MongoRepository<Member, String> {
    Optional<Member> findByEmail(String email);
    List<Member> findAllByOrderByNameAsc();
}
```

### c. Service Layer

- Create a `@Service` for business logic.

### d. Controller Layer

**Replace JAX-RS with Spring Boot's REST controller:**

```java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/members")
public class MemberRestController {
    private final MemberService memberService;

    @GetMapping
    public List<Member> listAllMembers() { ... }

    @GetMapping("/{id}")
    public Member getMemberById(@PathVariable String id) { ... }

    @PostMapping
    public ResponseEntity<?> createMember(@RequestBody @Valid Member member) { ... }
}
```
- Handle unique email exceptions gracefully (HTTP 409 Conflict).

### e. Configuration

```yaml
# application.yml

spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/kitchensinkdb
```

- Remove JPA/Hibernate dependencies.
- Add `spring-boot-starter-data-mongodb` and related dependencies.

---

## 4. MongoDB Dependencies

**Maven:**
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
<!-- For testing: -->
<dependency>
    <groupId>de.flapdoodle.embed</groupId>
    <artifactId>de.flapdoodle.embed.mongo</artifactId>
    <scope>test</scope>
</dependency>
```

---

## 5. MongoDB Initialization Script

**On first run, MongoDB creates the collection automatically; for initial data (optional):**

```js
// init-members.js
db = db.getSiblingDB('kitchensinkdb');
db.members.insertOne({
    name: "John Smith",
    email: "john.smith@mailinator.com",
    phoneNumber: "2125551212"
});
```
**Apply with:**
```bash
mongo < init-members.js
```

Or for test/dev: use a Spring Boot `data.sql`-like initializer.

---

## 6. Testing Strategy

**a. Unit & Integration Testing**

- Use JUnit 5/Spring Boot's `@SpringBootTest` for controller/repository/service tests.
- Use embedded MongoDB (`de.flapdoodle.embed.mongo`) for integration tests.

**b. Example Test Skeleton:**

```java
@SpringBootTest
@AutoConfigureDataMongo
class MemberRepositoryTests {

    @Autowired
    MemberRepository repository;

    @Test
    void testSaveAndFind() {
        Member m = new Member();
        m.setName("Test User");
        m.setEmail("test@example.com");
        m.setPhoneNumber("1234567890");
        repository.save(m);

        Member found = repository.findByEmail("test@example.com").orElseThrow();
        assertEquals("Test User", found.getName());
    }
}
```

**c. REST API Testing**

- Use MockMvc for controller testing.
- Test unique constraints, input validation, and REST API semantics.

---

## 7. Summary Table: Old vs. New

| Aspect                | Old Stack (JBoss+JPA/RDBMS)   | New Stack (Spring Boot+MongoDB)         |
|-----------------------|-------------------------------|-----------------------------------------|
| Persistence           | JPA/Hibernate, SQL            | Spring Data MongoDB                     |
| Entity                | `@Entity`                     | `@Document`                             |
| Primary Key           | `@Id @GeneratedValue` (Long)  | `@Id` (String/ObjectId or external Long)|
| Uniqueness            | DB Unique Constraint          | MongoDB Unique Index                    |
| Relationships         | -                             | -                                       |
| Queries               | JPQL/Criteria API             | Spring Data queries                     |
| Deployment            | JBoss, WEB-INF configs        | Standalone Spring Boot                  |
| REST                  | JAX-RS                        | @RestController                         |
| Validation            | Bean Validation (Jakarta)     | Bean Validation (Jakarta, Spring)       |
| Testing               | Arquillian/In-container       | JUnit + Embedded Mongo                  |

---

## Closing Notes and Further Reading

- If your data model becomes more complex, revisit MongoDB model for embedding/referencing.
- Carefully review authorization, validation, and exception handling in your API.
- **Consult Spring Data MongoDB documentation for advanced mapping/projected queries, validations, etc.**

---

**Happy migration!**

```