
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select destination
from "warehouse"."main"."stg_price_observations"
where destination is null



  
  
      
    ) dbt_internal_test