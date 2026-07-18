
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select route
from "warehouse"."main"."fct_price_observations"
where route is null



  
  
      
    ) dbt_internal_test