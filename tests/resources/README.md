# reusing / organising test-configurations
 
We started to organise test-configurations stored in the **tests/resources/** folder of the project.

I looked into what we had so far and the following convention fits:
 
* simple_cloudformation - a simple configuration to check the overall functionality
* sample_cloudformation - a realistic configuration like we would expect from a real service (make sure to clean up since leftovers could cause in unnecessary costs)
* special_cloudformation_what_is_it - configuration for special cases and want to reuse. 

