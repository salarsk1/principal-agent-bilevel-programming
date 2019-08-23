# Incentive design in principal-agent model with solving the Bilevel programming problem 

In this code we solve the principal-agent problem. The principal-agent problem is a bilevel programming problem where the principal design the contracts such that they maximizes their own utility while, they know that the agent seeks to maximize their own utilty. Therefore, the principal solves an optimization problem (leader problem) where one of the constraint is an other optimization problem (follower problem). Such problems are known as bilevel programming prolems.

If the follower optimization problem is a convex function, the common method is to replace this constraint with its KKT (Karush-Kuhn-Tucker) conditon. The KKT condition for convex problems is necessary and sufficient. However, for the non-convex problems the KKT condition is only a necessary condition and for this type of optimization problems it is not possible to replace them with the KKT condition. 

The follower optimization problem in our principal-agent problem is not a convex function. To solve the 
