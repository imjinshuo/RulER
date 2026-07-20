Each file named in the format "[source language]-[target language].txt" contains 100 selected RulER-mined translation rules from the [source language] to [target language], along with labels indicating whether they are correct.

For example:

```
Rule-x:
['expression_statement-0||||assignment_expression-0||||identifier-0||||=-0||||binary_expression-0||||array_access-0||||identifier-0||||[-0||||identifier-0||||]-0||||+-0||||decimal_integer_literal-0||||;-0', ['expression_statement-0||||assignment_expression-0||||identifier-0||||=-0||||binary_expression-0||||subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0||||+-0||||number_literal-0||||;-0']]
Source code:
index = a[i] + 1;
Target code:
<variable_1> = <variable_2>[<variable_3>]+<constant_1>;
Lable: 1
```
- **Rule-x** refers to the AST trees of the source and target statements defined by "Rule-x" in a depth-first search (DFS) sequence format.
- **Source code** refers to an example of the statement in the source programming language corresponding to the source AST structure of this rule.
- **Target code** refers to an example of the statement in the target programming language corresponding to the translation AST structure of this rule.
- **Lable** indicates whether Rule-id is correct based on manual inspection. A label of 1 represents correctness, while 0 represents an error.
