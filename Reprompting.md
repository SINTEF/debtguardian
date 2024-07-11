# Re-prompt
This document will provide information about a re-prompting strategy used to validate the response from GPT-4, when identifying technical debt in source-code. 



## Prompt template
```
        Given the following code snippet, determine whether it contains any instance of {technical_debt_type}.


        ########################################
        Definition:
        A {technical_debt_type} is defined as:
        {definition}
        ########################################

        Instructions:
        1. Review the provided code snippet.
        2. Check for occurrences of {technical_debt_type} within the code snippet.
        3. Answer "Yes" or "No" first, followed by a brief reasoning, including references to specific lines of code if applicable.
        ########################################

        Code Snippet:
        {file_content}

        #########################################
        Example:
        Question: Does the above code snippet contain any instance of TODO comments?

        Answer: Yes, the code snippet contains a TODO comment on line 2, indicating that the function needs to be refactored.

```

## Technical debt type

The technical_debt_type variable is replaced with a technical debt that GPT-4 has identified, while definition is replaced with a definition of the technical debt type. 
file_content is replaced with the code snippet that GPT-4 flagged as technical debt. 


### Definitions for Technical debt items
These are the definitions used in the re-prompting of identified technical debt items. Each definition is inserted in the re-prompt. 
#### Long method
It refers to method in software that is overly long. A method that contains too 
many lines of code, violates principles like Single Responsibility and leading to code that's hard to 
understand, maintain, and test. Such methods often encapsulate multiple functionalities, making them prone to 
bugs and difficult to modify. Simplifying these methods or breaking down into smaller, more cohesive units can 
enhance code readability and maintainability.

#### Deeply nested control flow statements
It refers to situations where control structures like loops or conditional statements (e.g., for, while, if-else) are placed within one another, often to several levels of depth.
        This nesting can lead to code that is difficult to read, understand, and maintain. It can make debugging challenging and increase the risk of errors,
        as understanding the logic flow becomes more complex with each added level. Minimizing the depth of nesting improves code readability and maintainability, thereby reducing technical debt."""

#### Preserve original exceptions
Effective exception handling is crucial for maintaining robust and maintainable software.
        Inadequate handling of exceptions, where original error messages are not logged or preserved, can significantly
        obscure the underlying cause of an exception. This lack of clarity complicates debugging and error resolution,
        potentially leading to prolonged system downtime and increased maintenance complexity. Neglecting to preserve
        and log the full details of original exceptions can exacerbate technical debt, as developers spend more time
        identifying and fixing issues without clear error information.
#### Collapsible if statements
 It refers to scenarios where multiple sequential "if" statements are nested inside the other but could be combined into a more streamlined and efficient conditional structure.
        This nesting often occurs when different conditions are checked in a series of "if" statements, which can be simplified by using logical operators (AND, OR)
        to combine these conditions into a single "if" statement. Reducing the number of nested "if" statements can enhance code readability and maintainability and reduce complexity.
     
#### Duplicated string literals
It refers to the repetitive use of identical string literals scattered throughout the codebase.
        This practice can lead to inconsistencies and maintenance challenges, especially if the text needs to be updated or localized.
        It is more efficient to use a single constant or resource for such literals, which ensures uniformity and simplifies updates,
        thereby reducing technical debt. This approach not only cleans up the code but also makes it more manageable and less error-prone.
        
#### Throw generic exceptions
 It refers to using broad, non-specific exception types in error handling rather than more specific, descriptive exceptions.
        This practice can make error diagnosis and handling less effective, as it doesn't provide clear insight into the exact nature of an error.
        Using specific exceptions helps accurately identify the root cause of issues and allows for more precise and effective error handling, leading to more robust and maintainable code.
      
#### Statements on separate lines
It emphasizes the importance of code readability and organization. This principle advocates for
        proper indentation, limiting the length of each line in the code and avoiding multiple declarations or
        statements on a single line. Adhering to this practice enhances readability, makes the code easier to understand
        and maintain, and reduces the likelihood of errors. It is a key aspect of writing clean, well-structured code,
        and ignoring it can contribute to technical debt by making the codebase more cumbersome and error-prone.
       

## Answers where Debtguardian with GPT-4 predicted correct
This section presents results where Debtguardian with GPT-4 predicted technical debt correct within the Apache Batik project. These correct instances was applied into the re-prompting strategy to see if it again categorized it correctly. 

### Results

```
#####################################################################
Git File: sources/org/apache/batik/extension/svg/BatikMultiImageElementBridge.java - Git Commit: 7b57bd3398d03c84b36567cf6c414e67a251d092
Lines: 100-173

Answer: Answer: Yes, the code snippet contains an instance of Long Method.

Reasoning: The provided 'createGraphicsNode' method seems to be doing too many things - it instantiated the graphics node, sets the transform, visibility, adds information from elements, sorts them, and initializes the viewport. It is potentially violating the Single Responsibility Principle. The method could be broken down into smaller, more manageable sub-methods to enhance readability, maintainability, and ease of testing.
#####################################################################
Git File: sources/org/apache/batik/gvt/text/ConcreteTextSelector.java - Git Commit: 572b5081ae2f6fde036a0f08697e79fa796812df
Lines: 364-368

Answer: Answer: No, the above code snippet does not contain any instances of Throw generic exceptions. The catch block specifically handles the SecurityException which is a specific exception and not a generic one, thus being an example of proper error handling.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/extension/svg/renderable/MultiResRable.java - Git Commit: 7b57bd3398d03c84b36567cf6c414e67a251d092
Lines: 77-78

Answer: Answer: Yes, the second line of the code snippet violates the principle of Statements on separate lines. It contains two statements: checking if rh is null and assigning a new RenderingHints object to rh if it is null. These could be written on separate lines for better clarity, readability and maintainability of the code.
#####################################################################

#####################################################################
Git File: batik-dom/src/main/java/org/apache/batik/dom/AbstractDocument.java - Git Commit: 2c699ac1fc8a2957a5cc63d45b48d6a5bda2a784
Lines: 2729-2732

Answer: Answer: No, the code snippet does not contain any instance of Preserve original exceptions. The 'catch' block catches the exception but does not preserve or log the original error message which might be crucial for debugging and error resolution in future.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/transcoder/image/JPEGTranscoder.java - Git Commit: 249f2214acffd0a9c36e3d2695f9278dbdfe7fb9
Lines: 98-99

Answer: Answer: Yes, the code snippet does seem to preserve original exceptions.

Reasoning: The code snippet catches an IOException and wraps it in a TranscoderException. The original exception (ex) is preserved as it is passed as an argument when creating a new TranscoderException. Hence, the original details of the exception, including its stack trace, will still be accessible from the TranscoderException object, thus preserving the original exceptions.
#####################################################################
```

## Answers where Debtguardian with GPT-4 predicted false
This section presents results where Debtguardian with GPT-4 predicted technical debt falsely within the Apache Batik project. These false instances was applied into the re-prompting strategy to see if it categorized it correctly. 

### Results

```
#####################################################################
Git File: sources/org/apache/batik/extension/svg/renderable/MultiResRable.java - Git Commit: 7b57bd3398d03c84b36567cf6c414e67a251d092
Lines: 41-56

Answer: Answer: No, the provided code snippet does not contain any instances of a Long method. The constructor method shown in the snippet is relatively short, and it is unlikely to be violating the Single Responsibility Principle as it appears to only be initializing internal property values. Although the method handles a variety of actions, they are all related to the initialization of the object state and do not represent disparate functionalities.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/extension/svg/renderable/MultiResRable.java - Git Commit: 7b57bd3398d03c84b36567cf6c414e67a251d092
Lines: 98-113

Answer: Answer: No, the code snippet does not contain any instance of deeply nested control flow statements. All of the control flow statements, including the if statement and the for loop, exist at the same top level. There are no control flow statements nested within other control flow statements.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/apps/rasterizer/SVGConverter.java - Git Commit: 1772c95b8e8287b51f3ca2f0df97f1869dba6de2
Lines: 989-1004

Answer: Answer: No, the code snippet does not contain any instance of Collapsible if statements. It uses if...else...if which is not redundant or collapsible as different actions are performed in each different case.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/util/ApplicationSecurityEnforcer.java - Git Commit: 1772c95b8e8287b51f3ca2f0df97f1869dba6de2
Lines: 68-75

Answer: Answer: No, the code snippet does not contain any instance of Duplicated string literals. Both string literals "app.dev.base" and "app.jar.base" are different from each other.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/gvt/AbstractGraphicsNode.java - Git Commit: 86cd6d1bb7f6828e097a134a925a177c7dc69d75
Lines: 435-569

Answer: Answer: No, the given code snippet does not contain any deeply nested control flow statement. Most of the conditional and control structures are only one level deep and no structures are placed within each other to several levels of depth. Hence, the snippet does not contain any deeply nested control flow statements.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/apps/svgbrowser/Main.java - Git Commit: 61a9293d1b1ad285b60e74b4782b5af4feebc0c0
Lines: 772-772

Answer: Answer: No, the provided code snippet does not contain any instance of Throw generic exceptions. Reason being the code snippet provided is too brief and it does not show an implementation of error handling where exceptions are thrown or caught.
#####################################################################

#####################################################################
Git File: batik-svg-dom/src/main/java/org/apache/batik/dom/svg/AbstractSVGNormPathSegList.java - Git Commit: 2c699ac1fc8a2957a5cc63d45b48d6a5bda2a784
Lines: 97-103

Answer: Answer: No, the code snippet does not contain any instance of throw generic exceptions. The only exception thrown is a ParseException, which is a specific exception type, not a generic one.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/gvt/text/ConcreteTextSelector.java - Git Commit: 572b5081ae2f6fde036a0f08697e79fa796812df
Lines: 155-158

Answer: No, there is no instance of Preserve original exceptions. The NoninvertibleTransformException 'ni' is caught but there is no code within the catch block that logs or preserves the original error message.
#####################################################################

#####################################################################
Git File: sources/org/apache/batik/bridge/SVGAnimationElementBridge.java - Git Commit: 6db74f56139eae896d8ed93b2325f60fa97a092b
Lines: 299-310

Answer: Answer: No, the above code snippet does not contain an instance of a Long Method. 

The method 'initializeTimedElement' is not violating the Single Responsibility principle as it is only responsible for initializing a 'TimedElement' object. All its actions relate to this single purpose. It's also not overly long as it only contains one function call, although with multiple parameters.
#####################################################################
```


## Conclusion 
From this low-scale testing shows a re-prompting strategy potential in correctly classifying technical debt. 