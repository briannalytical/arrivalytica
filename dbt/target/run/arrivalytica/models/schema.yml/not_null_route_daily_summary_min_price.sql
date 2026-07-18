
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select min_price
from "warehouse"."main"."route_daily_summary"
where min_price is null



  
  
      
    ) dbt_internal_test