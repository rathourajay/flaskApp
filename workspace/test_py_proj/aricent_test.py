def jfactor_and_number(jfactor_list, total_steps):
#     print jfactor_list
#     print total_steps
#     for step_num in range(11):
    jump_count = 0
    step_num = 1
    for i in range(len(jfactor_list)-1):
        print "step_num",step_num,"jfact_val",jfactor_list[i]
        if (step_num + jfactor_list[i]) < 11:
            
            possb_reach_steps = step_num + jfactor_list[i]  
            
            print "possb_reach_steps",possb_reach_steps
            
            inner_list = []
            
            index_start = step_num
            
            index_last = possb_reach_steps
            
            for j in range(index_start,index_last):
                inner_list.append(jfactor_list[j]) 
                
            print inner_list
#             for item in inner_list:
            choosen_jfacotr_val = max(inner_list)
            max_step_no = choosen_jfacotr_val.index()    
                
            jfact_val = jfactor_list[step_num]
            
            jump_count += 1
            
            step_num += 1
        else:
            print jump_count
            break
            
    
    
    
    

     
    
    

if __name__ == '__main__':
    jfactor_list = [1,3,3,4,2,2,9,7,6,8,9]
    total_steps  = 11
    jfactor_and_number(jfactor_list, total_steps)