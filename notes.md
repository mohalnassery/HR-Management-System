general tab rename to Employee information:
there will be 2 tabs:
1. general
    - add employee picture
    - add probation
    (reorganize the fields with categories in the webpage)
2. employment
    - remove rejoined date
    - remove probation (switch it to general tab)
    - remove in probation
    - remove is manager
    - remove payroll and merge it with cost center
    - cost center and profit center will have drop down list of all available cost centers (both from same table/ options (include in db so then we can add more if needed `cost_and_profit_centers`))
    - Cost center
    - Profit center
    - Employee category will be ( general, supervisor, manager, executive)

    (reorganize the fields with categories in the webpage)








Visa & Accommodation
- add company accommodations lists ( need to make db for accomodations, then we choose) 
    - can choose from already existing or add new one (choose from country to flat number so select the country then choose the city then choose the building number then choose the flat number) based on what we have in db
    - accomodation should have:
        - accomodation name
        - accomodation address
            - accomodation flat number
	        - accommodation Floor
            - accomodation building 
            - accomodation city
            - acommodation country


- add visa cr number
- add sponsor name
- add accommodation occupation date




delete bond tab and put it in another page with bond and guarantee (separate page)
- this will be another tab system to track all bonds and guarantees and their status


in add document http://0.0.0.0:8000/employees/1/documents/add/
- (Document type*) remove Gate Pass and CV 
- remove profession/title


in Contract & Accruals we will remove it as we have contract in documents tab


in offences we will do this:
- it will list all offences for the employee
- option to add offence:       
    - Ref No.
    - Entered On
    - Offence Type
        - Others
        - ACCEPTED lateness
        - Misuse of Property
        - USING MOBILE DURING DUTY HOURS
        - ABSENT WITHOUT REASON
        - LATNESS WITHOUT VALID REASON
        - PROPERTIES DAMAGE
        - BAD ATTITUDE WITH CO-WORKERS
        - BAD ATTITUDEWITH CUSTOMERS
        - NOT FOLLOWING ORDERS        
    - Total Value
    - Details
    - Offence Start Date
    - Offence End Date
- for each offence we will be able to:
    - documents related to the offence



in dependents we will do this:
- it will list all dependents for the employee (table view)
- option to add dependent: 	
    - Name
    - Relation (spouse, child, parent, sibling, other)
    - Date of Birth
    - Passport Number
    - Expiry Date
    - CPR Number
    - Expiry Date
    - Valid Passage?

(clicking on the dependent name will show the documents related to the dependent)
- for each dependent we will be able to upload:
    - documents related to the dependent
        - document Name
        - document Type (passport, ID, etc.)
        - document Number (for passport, ID, etc.)
        - document File (upload or scan similar to documents tab)
        - issue date
        - expiry date
        - Country of origin with list of all countries
        - Document Status (Valid, Expired, etc.) (auto update based on expiry date, if empty then valid)



general
bank 
documents
salary
depndents
assets in hand
offences