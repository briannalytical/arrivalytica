
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select depart_date
from "warehouse"."main"."stg_price_observations"
where depart_date is null



  
  
      
    ) dbt_internal_test