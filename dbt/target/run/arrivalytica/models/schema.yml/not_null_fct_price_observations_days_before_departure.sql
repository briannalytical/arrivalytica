
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select days_before_departure
from "warehouse"."main"."fct_price_observations"
where days_before_departure is null



  
  
      
    ) dbt_internal_test