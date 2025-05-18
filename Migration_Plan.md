# Migration Plan: Java to Spring Boot with MongoDB

## Project Analysis

## Migration Plan

Certainly! Here is a **detailed migration plan** (suitable for a README.md file) for converting the given Java EE kitchensink project running on JBoss EAP + relational database to a **Spring Boot + MongoDB** stack. This guide is targeted at Java developers experienced with enterprise apps who want to modernize their codebase.

---

# Migration Plan: From JBoss EAP/Java EE Kitchensink to Spring Boot + MongoDB

This document outlines how to migrate the kitchensink project from a traditional Jakarta EE (JBoss EAP, JSF, JAX-RS, CDI, JPA, EJB, H2 DB) stack to the modern Spring Boot ecosystem, using MongoDB as the persistence layer. This plan assumes the latest LTS Java (21) and the latest Spring Boot release.

---

## Table of Contents

1. [Set Up New Spring Boot Project](#1-set-up-new-spring-boot-project)
2. [Migrate Java Classes to Spring Boot](#2-migrate-java-classes-to-spring-boot)
3. [Switch from Relational Database to MongoDB](#3-switch-from-relational-database-to-mongodb)
4. [Required Configuration Changes](#4-required-configuration-changes)
5. [Updating the Build Process](#5-updating-the-build-process)
6. [Testing Considerations](#6-testing-considerations)
7. [Miscellaneous Notes and Recommendations](#7-miscellaneous-notes-and-recommendations)

---

## 1. Set Up New Spring Boot Project

**a. Create a new Project (Recommended: Maven):**
- Use [Spring Initializr](https://start.spring.io/)
  - Project: Maven
  - Java: 21
  - Dependencies:
    - Spring Web (REST API)
    - Spring Data MongoDB
    - Spring Boot DevTools (optional, for development)
    - Spring Validation
    - Lombok (optional, if you want to reduce boilerplate)
    - Thymeleaf (only if replacing JSF with a template engine; otherwise, ignore for pure API)
    - Test: JUnit, Spring Boot Starter Test
- Set group and artifact IDs accordingly (e.g., `org.yourorg.kitchensink`).

**b. Directory structure:**
```plaintext
src/
  main/
    java/org/yourorg/kitchensink
      controller/
      data/
      model/
      service/
      rest/
      ...
    resources/
      application.yml (or .properties)
  test/
    java/org/yourorg/kitchensink/
```

---

## 2. Migrate Java Classes to Spring Boot

### a. Entities → MongoDB Documents

- `Member` in `model/Member.java`
  - Replace all `@Entity`/`@Table` annotations with Spring Data MongoDB annotations.
  - Use `@Document(collection="members")`.
  - Replace `@Id`, `@GeneratedValue` as per Mongo conventions (String/ObjectId ids).
  - Validation annotations (`@NotNull`, `@Size`, etc.) are still supported with Spring's bean validation.

**Example:**
```java
@Document(collection = "members")
public class Member {
    @Id
    private String id; // Mongo IDs are Strings (usually ObjectId)

    @NotNull
    @Size(min = 1, max = 25)
    private String name;

    @NotNull @Email
    private String email;

    @NotNull
    @Size(min = 10, max = 12)
    private String phoneNumber;

    // getters & setters
}
```

### b. Data Access Layer

- JPA-based `MemberRepository` → Spring Data MongoDB Repository.
- Extend `MongoRepository<Member, String>`. Spring Data provides CRUD operations out-of-the-box.
- Custom queries use method naming conventions or `@Query` annotations.

**Example:**
```java
@Repository
public interface MemberRepository extends MongoRepository<Member, String> {
    Optional<Member> findByEmail(String email);
    List<Member> findAllByOrderByNameAsc();
}
```

- Remove all uses of JPA's `EntityManager`, Criteria APIs, and persistence context.

### c. Service Layer

- `@Stateless` EJB (`MemberRegistration`) → `@Service`
- For transactions (not needed for basic Mongo operations, but you can use `@Transactional` if needed).
- Use constructor or field injection (`@Autowired`).
- For event publication (CDI events): if required, use Spring's `ApplicationEventPublisher`/`@EventListener` (for now, you can simply call update logic directly unless you require decoupling).
- Replace logger injection with SLF4J (`LoggerFactory.getLogger(this.getClass())`). Spring uses SLF4J by default.

### d. Controller Layer

- JSF managed beans (`@Model`, `@Named`, etc.) for forms → Spring MVC `@RestController` or `@Controller` classes.
- JAX-RS REST endpoints → Spring `@RestController`
    - Replace `@Path`, `@GET`, `@POST` etc. with `@RequestMapping`, `@GetMapping`, `@PostMapping`.
    - Use validation: `@Valid` in method params.
    - Error handling: Use `@ExceptionHandler`, `@ControllerAdvice` for global error handling.
- FacesContext (JSF) messaging → standard web response messages/exceptions.

---

## 3. Switch from Relational Database to MongoDB

### a. Update Data Model:

- Remove all SQL/JPA constructs and annotations not supported by MongoDB or Spring Data Mongo.
- Replace `Long` IDs with `String` (MongoDB `ObjectId`). You can use custom IDs if needed.
- Compound/unique constraints:
  - MongoDB supports [unique indexes](https://docs.mongodb.com/manual/core/index-unique/), but you must create them via code or by configuring the collection.
  - Email uniqueness: check in service before insert, or create unique index on `email`.

### b. Replace Data Access Logic:

- All queries switch from JPQL or Criteria API to MongoRepository methods.

### c. Data Initialization:

- `import.sql` is not supported with MongoDB.
- Use `CommandLineRunner` or `data.mongodb.initialization.enabled` property and a `data.json` file for initial data, or a custom migration tool like [Mongock](https://mongock.io/).

---

## 4. Required Configuration Changes

### a. application.yml / application.properties

- Remove JPA/Hibernate configs.
- Add MongoDB configs:
    ```yaml
    spring:
      data:
        mongodb:
          uri: mongodb://localhost:27017/kitchensink
    ```
    Or use username/password, etc., if needed.

### b. Remove unnecessary descriptors

- Remove JPA `persistence.xml`, `*-ds.xml` files, and old server-side descriptors.
- `beans.xml`, `faces-config.xml` are not needed in Spring.
- Any JSF configuration can be omitted unless you plan to migrate UI to Thymeleaf.

---

## 5. Updating the Build Process

### a. Maven

- Remove all Java EE and JBoss-specific dependencies, BOMs, and plugins from `pom.xml`.
- Add:
  - `spring-boot-starter-parent`
  - `spring-boot-starter-web`
  - `spring-boot-starter-data-mongodb`
  - `spring-boot-starter-validation`
  - (optional) `spring-boot-starter-thymeleaf` if converting to Thymeleaf.
- Use the Spring Boot Maven Plugin for easy build/run:
  ```xml
  <plugin>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-maven-plugin</artifactId>
  </plugin>
  ```
- The project can be run with `mvn spring-boot:run`.

### b. Remove EAR/WAR packaging (unless you plan to deploy to a servlet container):

- Prefer `jar` and embedded Tomcat (default in Spring Boot).
- If WAR is required, configure as per [Spring Boot WAR deployment](https://docs.spring.io/spring-boot/docs/current/reference/html/deployment.html#deployment.war).

---

## 6. Testing Considerations

- Replace Arquillian and container-based tests with Spring Boot's integration and slice tests using JUnit 5 (Spring Boot Starter Test).
- Use embedded MongoDB for tests (e.g., [flapdoodle-embedded-mongo](https://github.com/flapdoodle-oss/de.flapdoodle.embed.mongo)) or testcontainers for integration tests.
- Migrate REST test clients to use Spring's `MockMvc` or WebTestClient.
- Any UI tests (JSF) should be rewritten for new UI layers or omitted if only a REST API is provided.

---

## 7. Miscellaneous Notes and Recommendations

- **UI Layer:**
  - If you migrate web front-end, consider using React/Vue/Angular (SPA) or a Spring Boot-friendly template engine like Thymeleaf or Freemarker (if you want to retain server-side rendering in Java).
  - There is no direct, easy JSF-equivalent in Spring; **do not attempt to migrate JSF pages as-is**.

- **Validation:**
  - Bean Validation annotations are supported via Spring's validation starter (JSR-380/JSR-303).
  - For REST endpoints, add `@Valid` to your input DTOs.

- **Event System:** 
  - Spring’s `ApplicationEventPublisher` can be used for events formerly implemented via CDI's `@Event`.
  - For simple update notifications, you may not need this.

- **Logging:** 
  - Use SLF4J/Logback—Spring sets this up for you.

- **REST API paths:** 
  - JAX-RS `/rest/members` becomes Spring Boot `/api/members` (suggest changing the base path to `/api` for clarity, but `/rest` is fine for migration).

- **Dependency Injection:** 
  - Continue using `@Service`, `@Repository`, `@Component`, and `@Autowired`.
  - No need for explicit `@Produces` or `@Named`; use constructor/final field injection when possible.

- **Transactions:** 
  - For MongoDB, transactions are rarely needed as most operations are atomic; use `@Transactional` only if doing multi-document transactions (requires replica set).

- **Unique constraints:** 
  - Ensure you add a MongoDB unique index for the `email` field (can use a CommandLineRunner on startup, or create manually in DB):
    ```java
    @Component
    public class MongoIndexCreator implements CommandLineRunner {
        private final MongoTemplate mongoTemplate;
        public MongoIndexCreator(MongoTemplate mongoTemplate) { this.mongoTemplate = mongoTemplate; }
        @Override
        public void run(String... args) {
            mongoTemplate.indexOps(Member.class)
                .ensureIndex(new Index().on("email", Direction.ASC).unique());
        }
    }
    ```
- **Initial Data:** 
  - For import data, use a Java-based initializer or `data.json` placed in `src/main/resources`.

---

## References

- [Spring Boot Reference Guide](https://docs.spring.io/spring-boot/docs/current/reference/html/application-properties.html)
- [Spring Data MongoDB Documentation](https://docs.spring.io/spring-data/mongodb/docs/current/reference/html/)
- [Upgrading to Spring Boot](https://spring.io/guides/gs/spring-boot/)
- [Migrating from Java EE to Spring Boot](https://reflectoring.io/java-ee-to-spring/)
- [Spring Boot Testing](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.testing)

---

## Sample Mapping Table

|  Java EE Technology | Spring Boot Equivalent      | Notes                                                              |
|---------------------|----------------------------|--------------------------------------------------------------------|
| JAX-RS (`@Path`)    | Spring MVC (`@RestController/@RequestMapping`) | Migrate REST endpoints          |
| JPA + Entities      | Spring Data MongoDB        | Use @Document, remove RDB-specific annotations     |
| JSF                 | Thymeleaf OR SPA frontend  | No direct equivalent; recommend new frontend       |
| CDI (`@Inject`)     | Spring Dependency Injection| Use `@Autowired`/constructor injection             |
| EJB (`@Stateless`)  | `@Service`/`@Transactional`| Use plain Service classes (transactions rarely used for Mongo) |
| Arquillian/JUnit    | Spring Boot Test/JUnit5    | Use Spring Boot testing tools & embedded Mongo     |

---

## Migration Cheat-Sheet

1. Set up a new Spring Boot project with MongoDB.
2. Port your business model (entities) as MongoDB Documents.
3. Port repositories to extend Spring Data MongoDB Repositories.
4. Port service classes, replacing EJBs.
5. Replace REST endpoints with `@RestController`.
6. Drop all JSF and JavaEE configs—replace (if needed) with a new UI.
7. Configure MongoDB connection in `application.yml`.
8. Use CommandLineRunner or other initializers for DB indexes and seed data.
9. Remove all JBoss, Weld, persistence, and faces config files.
10. Refactor and port tests to Spring Boot Test with embedded Mongo.

---

**You can further script or automate certain portions of this process via your Python migration tool, using the steps and explanations above as content for the generated README.**

## Suggested MongoDB Schema

```markdown
# kitchensink: Migration Plan to Spring Boot & MongoDB

## Overview

This document details the migration plan for the kitchensink Jakarta EE/JBoss application (currently using JPA/Hibernate/H2/Relational DB) to a modern Spring Boot (Java 21) application using MongoDB as the data store. It covers:

- Mapping the current data model to MongoDB schema
- Refactoring steps needed in Java codebase
- MongoDB schema, indexing, and initialization
- Embedded vs. referenced data models for MongoDB
- Data transformation requirements
- Spring Boot & MongoDB dependencies
- Recommendations and implementation order
- Testing and validation

---

## 1. Current Application Data Model & Key Code

**Entity: `Member`**
- Fields: `id`, `name`, `email`, `phoneNumber`
- Unique constraint: `email`
- JPA/Hibernate annotations for entity management
- Used in MemberController, REST endpoints, repository/services

**Repository Layer:**
- `MemberRepository` uses JPA's EntityManager for CRUD and queries
- Used to query by email, id, retrieve all ordered by name

**Business Logic:**
- `MemberRegistration` uses EntityManager to persist Member

**REST Layer:**
- `/rest/members` endpoint provides CRUD and list ops

**SQL Structure (`import.sql`):**
- Table: Member (`id: Long`, `name: String`, `email: String`, `phoneNumber: String`)
- email: unique

---

## 2. Migration Plan Overview

- Replace JPA/Hibernate layer with Spring Data MongoDB repositories
- Refactor domain to use MongoDB document mapping (`@Document`)
- Replace H2/Relational logic with MongoTemplate/MongoRepository
- Adjust persistence configuration and property files for MongoDB
- Ensure unique constraints & validation are handled
- Amend REST/resource layers to call MongoDB repository
- Provide MongoDB collection initialization/seed script for testing

---

## 3. **Files & Code to Update/Replace**

**Java Source:**

| Old File/Class                        | Replace/Rewrite as                                                       |
|---------------------------------------|--------------------------------------------------------------------------|
| src/main/java/org/.../Member.java     | Add `@Document`, adjust id type, update validation as POJO               |
| MemberRepository.java                 | Replace JPA repo with Spring Data `MemberRepository extends MongoRepository` |
| MemberRegistration.java               | Use MongoRepository for persistence                                      |
| Controller/REST Service Layer         | Minor: update dependency injection/use MongoDB-backed repo               |
| persistence.xml, XML config           | Remove, replace with application.properties for Mongo                     |
| Resources.java                        | Remove EntityManager/JPA logic                                           |
| Test Files (Integration Tests)        | Adapt to use MongoDB (`@DataMongoTest` etc.)                             |

**Configuration:**

| Old File                             | Replace with                 |
|--------------------------------------|------------------------------|
| persistence.xml, datasources.xml     | application.properties for MongoDB host, DB, etc.|
| import.sql                           | MongoDB JSON seed script or Java @PostConstruct  |

---

## 4. MongoDB Schema Design

### **4.1. Recommended MongoDB Collection Schema**

#### 1. **Collection: `members`**

Sample Document:
```json
{
  "_id": ObjectId("..."),
  "name": "John Smith",
  "email": "john.smith@mailinator.com",
  "phoneNumber": "2125551212"
}
```

- `email`: must be unique (MongoDB unique index)
- `phoneNumber`: string, validation can be done at application level
- No need for references/embedding — this collection is self-contained

#### 2. **Java Domain (`Member.java`)**

- Annotate with `@Document(collection = "members")`
- Use `@Id` from Spring Data, which maps to MongoDB’s `_id` (can use `String` or `ObjectId`)
- Use validation annotations (`@Email`, `@NotEmpty`, etc.) as before

#### 3. **MongoRepository**

```java
public interface MemberRepository extends MongoRepository<Member, String> {
    Optional<Member> findByEmail(String email);
    List<Member> findAllByOrderByNameAsc();
}
```

#### 4. **Indexing**

- Ensure unique index on `email`
  ```java
  @CompoundIndexes({
    @CompoundIndex(name = "email_unique_idx", def = "{'email' : 1}", unique = true)
  })
  public class Member { ... }
  ```

#### 5. **Initialization Script**

For importing initial data:
```json
[
  {
    "name": "John Smith",
    "email": "john.smith@mailinator.com",
    "phoneNumber": "2125551212"
  }
]
```
Import with `mongoimport --db kitchensink --collection members --file init_members.json`

---

## 5. **Embedded vs. Referenced Docs**

No sub-entities to embed; all fields are simple and belong to the `Member` document. No separate collections/references needed.

---

## 6. **Indexing Strategy**

- Unique index on `"email"` (enforced both via MongoDB and in the repository/service)
- Optionally, an index on `"name"` for search/sort performance

---

## 7. **Configuration Changes**

**Spring Boot `application.properties`:**
```properties
spring.data.mongodb.uri=mongodb://localhost:27017/kitchensink
spring.data.mongodb.database=kitchensink
# (Optional) server port, logging, etc
```

Remove all JPA, Hibernate, and relational DB configs.

---

## 8. **Data Transformation Plan**

- Export existing data (`Member`) from RDBMS to flat JSON for import into MongoDB.
  - Convert column names to field names as per POJO
  - Remove any surrogate keys if not needed or let MongoDB generate new `_id`
  - Ensure "email" uniqueness

---

## 9. **Implementation Steps (Detailed)**

### **1. Setup Spring Boot Project**

- Use [Spring Initializr](https://start.spring.io/):
  - Dependencies: Spring Web, Spring Data MongoDB, Validation, (optionally Lombok)
  - Set Java version to 21

### **2. Copy & Refactor Domain**

- Add `@Document("members")` to `Member`
- Change id to `@Id String id` (or ObjectId)
- Keep all necessary validation annotations

### **3. Replace Repository Layer**

- Implement Spring Data `MemberRepository extends MongoRepository<Member, String>`
- Refactor custom JPA queries as MongoDB query methods

### **4. Refactor Service Layer**

- Replace direct use of EntityManager with `memberRepository.save(member);`
- Adjust event mechanics if needed; for simple apps, repo save is enough

### **5. Update REST/Controller Layer**

- Change JAX-RS/Jakarta annotations to `@RestController`, `@GetMapping`, etc.
- Inject repository/service as `@Autowired`
- Adjust response handling to match Spring idioms

### **6. Remove Legacy Java EE/JBoss/JPA Artifacts**

- Delete/ignore persistence.xml, beans.xml, all JPA/Hibernate config
- Remove DS XMLs

### **7. Apply MongoDB Indexes**

- In domain (`Member.java`) use `@CompoundIndex` or create indexes on startup
- Optionally add an ApplicationRunner to ensure index creation

### **8. Write MongoDB Seed Script**

- Use `mongoimport`, or write a Spring `@Component` to preload data at startup

### **9. Update Tests**

- Replace Arquillian/JBoss tests with Spring Boot test classes
- Use `@DataMongoTest` for repository, `@SpringBootTest` for integration tests
- Use embedded MongoDB (Flapdoodle) for tests

### **10. Update Build/Deployment Artifacts**

- Use Maven with `spring-boot-starter-parent`
- Remove JBoss profiles, old plugins

---

## 10. **MongoDB Dependencies (Maven)**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
<!-- Optional: Lombok, Web -->
```

---

## 11. **Sample MongoDB Initialization Script**

**init_members.json**
```json
[
  {
    "name": "John Smith",
    "email": "john.smith@mailinator.com",
    "phoneNumber": "2125551212"
  }
]
```
Import:
```bash
mongoimport --db kitchensink --collection members --file init_members.json --jsonArray
```

Or (in Spring Boot):
```java
@Component
public class DataSeeder implements CommandLineRunner {
    @Autowired MemberRepository repo;
    public void run(String... args) {
        if (repo.count()==0) {
            repo.save(new Member(null,"John Smith","john.smith@mailinator.com","2125551212"));
        }
    }
}
```
---

## 12. **Testing Strategy**

- Unit test: all repository methods (`findByEmail`, `findAllByOrderByNameAsc`)
- Integration test: REST endpoints using MockMvc/RestTemplate
- Use embedded MongoDB (`@DataMongoTest`)
- Test email uniqueness — attempt duplicate, expect exception
- Test validation (missing name/email/phoneNumber)
- Test query result ordering
- Test seed data load on startup

---

## 13. **Recommendations & Best Practices**

- Keep the `members` collection flat unless more complex relations arise
- Always enforce unique index on `email`
- Handle domain validation at application level
- Use DTOs to avoid exposing internal MongoDB document structure via REST
- Use standard error handling for unique/validation errors (HTTP 409, 400)
- Document which fields are indexed and why in README codebase

---

## 14. **Summary Checklist**

- [ ] Create Spring Boot project & switch all config to application.properties
- [ ] Convert `Member` entity to Spring Data document
- [ ] Replace all persistence layer code with MongoRepository
- [ ] Apply unique index on email via annotation or startup code
- [ ] Refactor controllers/services to use Spring MVC/Spring Data
- [ ] Remove all JPA/Hibernate config
- [ ] Provide MongoDB seed/init script for members
- [ ] Update/build and test using embedded MongoDB
- [ ] Document migration in README (this file!)

---

## 15. **References**

- [Spring Data MongoDB Reference](https://docs.spring.io/spring-data/mongodb/docs/current/reference/html/)
- [MongoDB Unique Indexes](https://www.mongodb.com/docs/manual/core/index-unique/)
- [Spring Boot with MongoDB Guide](https://spring.io/guides/gs/accessing-data-mongodb/)

---

## Appendix: Example Spring Boot Entity

```java
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import jakarta.validation.constraints.*;

@Document("members")
@CompoundIndex(name = "email_unique_idx", def = "{'email': 1}", unique = true)
public class Member {
    @Id
    private String id;

    @NotNull @Size(min = 1, max = 25)
    private String name;

    @NotNull @NotEmpty @Email
    private String email;

    @NotNull @Size(min = 10, max = 12)
    @Pattern(regexp = "\\d{10,12}")
    private String phoneNumber;
    // getters/setters ...
}
```

---

**Following these steps will result in a clean, efficient migration of the kitchensink application to a modern Spring Boot & MongoDB stack, ready for cloud-native use!**
```
