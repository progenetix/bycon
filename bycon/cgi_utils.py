import cgi, cgitb

################################################################################

def cgi_parse_query():

    form_data = cgi.FieldStorage()
    return(form_data)

################################################################################

def cgi_exit_on_error(shout):

    print("Content-Type: text")
    print()
    print(shout)
    exit()

