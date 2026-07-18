
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select origin
from "warehouse"."main"."stg_price_observations"
where origin is null



  
  
      
    ) dbt_internal_test