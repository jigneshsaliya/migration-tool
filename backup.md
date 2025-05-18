# Migration Plan: Java to Spring Boot with MongoDB

## Project Analysis

## Migration Plan

Certainly! Here is a detailed **migration plan** you should generate in your tool for converting the given JBoss EAP "kitchensink" application to a modern **Spring Boot** application using **MongoDB**.

---

# Migration Plan: From JBoss EAP (Jakarta EE + RDBMS) to Spring Boot + MongoDB

This migration guide helps you modernize the "kitchensink" application from running on JBoss EAP with a relational database to **Spring Boot (Java 21) and MongoDB**.

---

## 1. **Set up a New Spring Boot Project**

- **Create a new project** using [Spring Initializr](https://start.spring.io/):
  - **Language**: Java
  - **Java version**: 21
  - **Build Tool**: Maven (or Gradle)
  - **Dependencies**:
    - Spring Web
    - Spring Data MongoDB
    - Spring Boot DevTools
    - Spring Validation
    - (Optional) Spring Boot Starter Test

- **Directory Structure**  
  Organize your packages following best Spring Boot practices, e.g.:
  ```
  src/main/java/com/example/kitchensink/
      controller/
      model/
      repository/
      service/
      config/
  ```
  (You may copy over the 'webapp/resources' to the new project if you keep some static content.)

---

## 2. **Migrating Existing Java Classes to Spring Boot Components**

**Overview:**  
Ma jority of Jakarta EE concepts (e.g. `@Entity`, `@Inject`, `@Stateless`, `@RequestScoped`) must be mapped to Spring Boot paradigms.

### a. **Model Classes**
- **Member.java**
  - Remove JPA annotations (`@Entity`, `@Table`, `@Id`, etc).
  - Annotate with `@Document(collection = "members")` from `org.springframework.data.mongodb.core.mapping.Document`.
  - Change the `id` field to `@Id` from `org.springframework.data.annotation.Id` (type: `String` or `ObjectId`).
  - Bean validation annotations (`@NotNull`, `@Size`, `@Email`, etc) remain compatible (Spring Boot uses the same JSR 380 / Hibernate Validator).
  - Remove any JPA-specific imports and annotations.

### b. **Repositories**
- **MemberRepository.java**
  - Convert to a Spring Data MongoDB repository interface:
    ```java
    public interface MemberRepository extends MongoRepository<Member, String> {
        Optional<Member> findByEmail(String email);
        List<Member> findAllByOrderByNameAsc();
    }
    ```
  - Remove JPA Criteria/EntityManager logic. Use method query derivation (as above) with Spring Data.

### c. **Service Layer**
- **MemberRegistration.java**
  - Change `@Stateless` EJB to `@Service` (`org.springframework.stereotype.Service`).
  - Use constructor or field injection (`@Autowired`) for dependencies.
  - Replace `EntityManager.persist()` with `memberRepository.save(member)` (inject the repository).

### d. **Controller / REST Layer**
- **MemberController.java**
  - Change from JSF controller to a `@RestController` or (if you want to keep forms) a Spring MVC `@Controller`.
  - For REST, implement endpoints in a class annotated with `@RestController`, mapping paths with `@RequestMapping`/`@GetMapping`, etc.

- **REST Resources (JaxRsActivator.java, MemberResourceRESTService.java)**
  - In Spring Boot, there is no need for `JaxRsActivator.java`.
  - All RESTful endpoints reside in regular `@RestController` classes.
  - For example:
    ```java
    @RestController
    @RequestMapping("/api/members")
    public class MemberRestController {
        // endpoints for listing, creating, fetching etc.
    }
    ```

### e. **CDI / Producer Beans / Event**
- Replace CDI concepts with Spring equivalents:
  - `@Produces` → handled by `@Bean` methods or simply as `@Component/@Service` beans.
  - `@Inject` → `@Autowired` (or constructor injection).
  - `@Event` → Spring's `ApplicationEventPublisher` (if still needed for decoupling events).

### f. **Faces/JSF**
- JSF (Facelets/XHTML) is not natively supported in Spring Boot. Modernize to a frontend framework (like Thymeleaf or a client-side SPA), or use Spring Boot MVC with JSP/Thymeleaf.
- **If keeping web UI:**  
  - Port `.xhtml` files to Thymeleaf templates, updating EL expressions from `#{}` to `${}` as used in Spring.
  - Otherwise, consider exposing only REST endpoints and building a frontend separately.

---

## 3. **Switching Database: From Relational to MongoDB**

- **Remove all usage of JPA** (`EntityManager`, `@Entity`, `persistence.xml`, etc).

- **Model changes:**
  - The `@Id` field may change from `Long` to `String`/`ObjectId` for Mongo compatibility.
  - Ensure objects can safely be stored as documents (Spring Data MongoDB handles POJOs).

- **Repository changes:**
  - Extend from `MongoRepository` or `CrudRepository`.
  - Query methods follow method naming conventions as described above.

- **Unique Fields:**  
  - MongoDB does not enforce JPA `@UniqueConstraint` annotation.  
    - Instead, ensure unique indexes are created for "email" (`@Indexed(unique=true)` in the model class).
    - Or, create indexes manually or via migration scripts.

- **Database Initialization:**  
  - Replace `import.sql` with:
    - [data initialization in Spring Boot](https://docs.spring.io/spring-boot/docs/current/reference/html/data.html#data.sql.mongo), by providing a `data.json` or `import.js` for Mongo.
    - Or insert documents via a CommandLineRunner bean.

---

## 4. **Configuration Changes**

- **application.properties / application.yml** in `src/main/resources`:
  - Define MongoDB connection:
    ```
    spring.data.mongodb.uri=mongodb://localhost:27017/kitchensink
    ```
  - Set other properties like `server.port`, etc.

- **Remove**:
  - `persistence.xml`
  - WildFly/JBoss data source XML files
  - CDI-related config files (beans.xml, etc) unless needed for JEE-specific logic

---

## 5. **Build Process & Project Metadata**

- Use **Spring Boot's plugin** for Maven/Gradle:
  - For **Maven**: Add the Spring Boot Maven Plugin to your `pom.xml`  
    ```xml
    <plugin>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-maven-plugin</artifactId>
    </plugin>
    ```
  - Remove WildFly/EAP/Jakarta EE parent POMs/deps.
  - Use standard Maven `spring-boot:run` to start the app.
- **Packaging**:  
  App is standalone (`jar` with embedded Tomcat/Jetty).

---

## 6. **Testing Considerations**

- **Unit Testing:**
  - Use JUnit 5 (`spring-boot-starter-test`).
  - For repository/integration tests, use [de.flapdoodle.embed.mongo](https://github.com/flapdoodle-oss/de.flapdoodle.embed.mongo) to spin up embedded MongoDB.

- **Integration Testing:**
  - Use `@SpringBootTest` for full-stack integration tests.
  - Update any Arquillian tests to regular Spring `@Test` classes, using `MockMvc` for controller layer and "testcontainers" or embedded Mongo for DB layer.

- **Remove Arquillian**
  - Arquillian is not used in Spring Boot; all test context managed using Spring's test support.

---

## 7. **Other Points & Recommendations**

- **Frontend:**  
  - If the previous UI was JSF, consider a modern alternative (Thymeleaf, React, Angular, etc).
  - If not migrating the UI, expose REST endpoints and instruct users to use Postman/curl or spend a phase on UI migration.

- **Bean Validation:**  
  - Remains mostly compatible; handled via Spring's validation infrastructure.

- **CDI Events:**  
  - Replace with Spring `ApplicationEventPublisher` or simply call listeners directly.

- **Transactional Operations:**  
  - In MongoDB, single-document ops are atomic; multi-document transactions need special support (and are available since MongoDB 4.x).

- **Logging:**  
  - Use Spring's logging abstractions (SLF4J, Logback).

---

## 8. **Sample Member Document (MongoDB)**

```json
{
  "_id": "665b6ecaab6f5b0e46e12e13",
  "name": "John Smith",
  "email": "john.smith@mailinator.com",
  "phoneNumber": "2125551212"
}
```

---

## 9. **References**

- [Spring Boot Documentation](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Spring Data MongoDB Reference](https://docs.spring.io/spring-data/mongodb/docs/current/reference/html/)
- [Migrating from JPA to MongoDB](https://docs.spring.io/spring-data/jpa/docs/current/reference/html/#jpa.repositories)

---

## 10. **Summary Table: Jakarta EE vs. Spring Boot (MongoDB)**

| Jakarta EE/EAP        | Spring Boot/MongoDB    |
|-----------------------|------------------------|
| Entity (`@Entity`)    | Document (`@Document`) |
| JPA Repo/EntityManager| `MongoRepository`      |
| EJB / @Stateless      | @Service               |
| JSF Controller (EL)   | @Controller/@RestController |
| JAX-RS (REST)         | Spring Web REST Controllers |
| Arquillian Tests      | Spring Boot Tests      |
| `persistence.xml`     | `application.properties` |
| SQL Seed/import.sql   | JSON/JS script/CommandLineRunner |

---

## 11. **Example Migration of "Member" Entity**

### *Jakarta EE JPA version:*
```java
@Entity
@Table(uniqueConstraints = @UniqueConstraint(columnNames = "email"))
public class Member implements Serializable {
    @Id
    @GeneratedValue
    private Long id;
    @NotNull @Size(min = 1, max = 25) private String name;
    @NotNull @NotEmpty @Email private String email;
    ...
}
```

### *Spring Boot Mongo version:*
```java
@Document("members")
public class Member {
    @Id
    private String id;
    @NotNull @Size(min = 1, max = 25) private String name;
    @NotNull @NotEmpty @Email private String email;
    ...
}
```

---

# Conclusion

Migrating from JBoss EAP to Spring Boot + MongoDB entails updating the codebase from JPA/JSF/EJB-centric design to Spring Boot's component and REST-based structure, modernizing the database layer, and configuring the application for a non-relational environment. This process, though straightforward, may require significant reorganization, especially if the UI was tightly coupled with JSF.

---

**Ensure you test each migration step, and consider automating database migration and initial data population for MongoDB using approaches native to Spring Boot.**

## Suggested MongoDB Schema

```markdown
# Migrating Kitchensink Example to Spring Boot + MongoDB

This document provides a detailed strategy to migrate the **kitchensink** application (originally developed on Jakarta EE/JBoss EAP with a relational database) to a modern stack using **Spring Boot** (Java 21) and **MongoDB**. It includes a MongoDB schema suggestion, migration steps, required code changes, and best practices for the new stack.

---

## 1. Overview of Current Application

- **Original Stack:** Jakarta EE (JPA, EJB, JSF), JBoss EAP, H2 (relational DB)
- **Core Entity:** `Member` (with fields: id, name, email, phoneNumber)
- **Layers Used:** MVC with RESTful API endpoints, persistence with JPA, Bean Validation
- **Objective:** Migrate to:
  - **Spring Boot** (latest stable, Java 21)
  - **MongoDB** (document DB replacing relational DB)
  - Modern, cloud-native, and maintainable codebase

---

## 2. MongoDB Migration Strategy

### a) **Java Files and Classes to Refactor**

| Original Java File/Class                                        | Notes/Action for Migration                              |
|:---------------------------------------------------------------|:--------------------------------------------------------|
| `src/main/java/org/jboss/as/quickstarts/kitchensink/model/Member.java`                  | Refactor as a Spring Boot @Document for MongoDB         |
| `src/main/java/org/jboss/as/quickstarts/kitchensink/data/MemberRepository.java`          | Rewrite as a Spring Data `MongoRepository`              |
| `src/main/java/org/jboss/as/quickstarts/kitchensink/service/MemberRegistration.java`     | Refactor as a Spring `@Service` or inside Controller    |
| `src/main/java/org/jboss/as/quickstarts/kitchensink/controller/MemberController.java`    | Rewrite as a Spring `@RestController` or `@Controller`  |
| `src/main/java/org/jboss/as/quickstarts/kitchensink/rest/MemberResourceRESTService.java` | Merge RESTful logic into Spring REST controller         |
| `src/main/java/org/jboss/as/quickstarts/kitchensink/util/Resources.java`                | Remove, handled by Spring's dependency injection        |

**Remove/Replace:**
- All usage of JPA and EntityManager
- EJB annotations and transaction demarcation (use Spring @Transactional)

---

## 3. Target MongoDB Schema Design

### a) **Original Relational Schema**

| Table   | Fields                                                                                         |
|:--------|:-----------------------------------------------------------------------------------------------|
| Member  | `id` (PK, auto), `name` (varchar, not null), `email` (varchar, not null, unique), `phone_number` (varchar, not null) |

### b) **Proposed MongoDB Collection: `members`**

#### **Sample Document Structure**

```json
{
  "_id": ObjectId("65d...1c1"),
  "name": "John Smith",
  "email": "john.smith@mailinator.com",
  "phoneNumber": "2125551212"
}
```

#### **Corresponding Spring Data Model**

```java
@Document(collection = "members")
@Data // Lombok or manually write getters/setters
@NoArgsConstructor
public class Member {
    @Id
    private String id;

    @NotBlank
    @Size(min = 1, max = 25)
    @Pattern(regexp = "[^0-9]*", message = "Must not contain numbers")
    private String name;

    @NotBlank
    @Email
    private String email;

    @NotBlank
    @Size(min = 10, max = 12)
    private String phoneNumber;
}
```

#### **Differences from the RDBMS Model**

- `id` will be a MongoDB ObjectId (string).
- Unique constraint on `email` will be implemented as a MongoDB **unique index**.
- No need for a separate `phone_number` column, field is stored as part of the document.
- All fields can use Bean Validation, as before.

---

## 4. Embedding vs. Referencing

- **Embedding:** Not needed, since `Member` has only simple fields.
- **Referencing:** No references required unless the domain expands.
- **If new entities require relationships:** Prefer embedding for tight, 1-to-1 or 1-to-few, and referencing for 1-to-many or many-to-many (in separate collections).

---

## 5. Indexing Recommendations

- **Unique Index** on `email` for fast lookup and uniqueness.
- **Optional:** Index on `name` for sorting if searching/filtering by name is common.

#### **How to create indexes in MongoDB:**
```javascript
db.members.createIndex({ email: 1 }, { unique: true });
db.members.createIndex({ name: 1 });
```

---

## 6. Configuration Changes

### a) **Spring Boot MongoDB Dependency**

Add to `pom.xml`:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

### b) **Application Config**

In `src/main/resources/application.properties`:

```properties
spring.data.mongodb.uri=mongodb://localhost:27017/kitchensink
server.port=8080

# (optional) Enable MongoDB auto-index creation
spring.data.mongodb.auto-index-creation=true
```

---

## 7. MongoDB Initialization Script (Seed Data)

`mongodb-init.js`:

```javascript
db = db.getSiblingDB('kitchensink');
db.members.insertOne({
  "name": "John Smith",
  "email": "john.smith@mailinator.com",
  "phoneNumber": "2125551212"
});
```

---

## 8. Detailed Implementation Steps

### **Step 1: Create a New Spring Boot Project (Java 21)**

- Use [Spring Initializr](https://start.spring.io/) or your IDE to create:
  - Java 21
  - Spring Web
  - Spring Data MongoDB
  - Spring Boot Starter Validation (optional: Lombok)
  - Group: `com.example`
  - Artifact: `kitchensink`

### **Step 2: Model Layer**

- Refactor `Member` class as shown above under Schema Design.
- Place in `com.example.kitchensink.model`.

### **Step 3: Repository Layer**

`MemberRepository.java`:
```java
public interface MemberRepository extends MongoRepository<Member, String> {
    Optional<Member> findByEmail(String email);
    List<Member> findAllByOrderByNameAsc();
}
```

### **Step 4: Service Layer (Optional, for business logic)**

`MemberService.java`:
```java
@Service
public class MemberService {
    @Autowired private MemberRepository memberRepository;

    public Member createMember(Member member) {
        // Additional business logic if necessary
        return memberRepository.save(member);
    }

    public List<Member> getAllMembers() {
        return memberRepository.findAllByOrderByNameAsc();
    }

    public Optional<Member> findById(String id) {
        return memberRepository.findById(id);
    }

    public boolean emailExists(String email) {
        return memberRepository.findByEmail(email).isPresent();
    }
}
```

### **Step 5: Controller Layer**

`MemberController.java` (REST Controller):

```java
@RestController
@RequestMapping("/api/members")
@Validated
public class MemberController {
    @Autowired private MemberService memberService;

    @GetMapping
    public List<Member> listAll() {
        return memberService.getAllMembers();
    }

    @GetMapping("/{id}")
    public ResponseEntity<Member> get(@PathVariable String id) {
        return memberService.findById(id)
               .map(ResponseEntity::ok)
               .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<?> create(@Valid @RequestBody Member member) {
        if (memberService.emailExists(member.getEmail())) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(Map.of("email", "Email taken"));
        }
        Member saved = memberService.createMember(member);
        return ResponseEntity.ok(saved);
    }
}
```

### **Step 6: Validation and Error Handling**

- Use `@Valid` on request payloads.
- Return 409 Conflict on duplicate email.
- Return 400 Bad Request for validation errors.

### **Step 7: Remove Old Artifacts**

- JSF, EJB, JPA code and configuration are no longer needed.
- Only REST/JSON endpoints required (UIs can be rewritten using React/Vue/Angular if needed).

---

## 9. MongoDB Dependencies

- **Production:** [MongoDB Community Server](https://www.mongodb.com/try/download/community)
- **Development/Test:** [Testcontainers](https://www.testcontainers.org/modules/databases/mongodb/) or `de.flapdoodle.embed.mongo` for embedded MongoDB during integration tests
- **Spring Boot:** As above in config section

---

## 10. Testing Strategy

- **Unit Tests:** For Service methods (using Mockito)
- **Integration Tests:** Use embedded MongoDB or TestContainers, and Spring Boot’s `@DataMongoTest` for repository layer
- **REST API Tests:** With MockMvc or REST-assured for controllers
- **Validation Tests:** Send invalid JSON payloads and ensure appropriate errors

---

## 11. Additional Recommendations

- Use [MongoDB validation](https://docs.mongodb.com/manual/core/schema-validation/) at the DB level (optional).
- For production, configure authentication on your MongoDB instance and set credentials in `application.properties`.
- Consider using DTOs (Data Transfer Objects) for separating API representation from persistence model if the domain grows.

---

## 12. Stretch Goal: Additional Collections Example

If your domain grows to include, for example, "Groups" with members, consider the following:

- Embed simple group information inside `Member` if group info is small/static.
- Use a separate `groups` collection, and reference members by their `_id` for many-to-many relationships.
- Use [MongoDB aggregation pipelines](https://docs.mongodb.com/manual/aggregation/) for reporting.

---

## Summary Table

| Relational Table | Mongo Collection | _id Type      | Uniqueness        | Indexes       | Notes                               |
|:-----------------|:----------------|:--------------|:------------------|:--------------|:------------------------------------|
| Member           | members         | ObjectId (str)| Email, Unique     | email (uniq), name (asc)| All member data in a single document |

---

## 13. References

- [Spring Data MongoDB Reference](https://docs.spring.io/spring-data/mongodb/docs/current/reference/html/)
- [MongoDB Schema Design Best Practices](https://www.mongodb.com/best-practices/schema-design)
- [Spring Boot Starter Guide](https://spring.io/guides/gs/spring-boot/)
- [Spring Boot and MongoDB Getting Started](https://spring.io/guides/gs/accessing-data-mongodb/)

---

## 14. Example Directory Layout

```
tool/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/example/kitchensink/
│       │       ├── model/Member.java
│       │       ├── repository/MemberRepository.java
│       │       ├── service/MemberService.java
│       │       └── controller/MemberController.java
│       └── resources/
│           └── application.properties
├── test/
│   └── ... (unit/integration tests)
├── mongodb-init.js
├── pom.xml
└── README.md (this document)
```

---

**By following these steps, you will achieve a clean migration of the Kitchensink example from a JBoss EAP/Jakarta EE monolith using a relational database to a modern, cloud-native Spring Boot application backed by MongoDB.**

```
