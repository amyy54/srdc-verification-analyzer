function dataFormParse()
{
    var redirect = window.location.href + "data/"

    var game = document.getElementById("abbreviation").value;
    redirect += game;
    var start_date = document.getElementById("start_date").value;
    var end_date = document.getElementById("end_date").value;
    var parse_other = document.getElementById("other_parse").checked;

    if (start_date)
    {
        redirect += "?startdate=" + start_date;
        if (end_date)
        {
            redirect += "&enddate=" + end_date;
            if (parse_other)
            {
                redirect += "&parseother=yes";
            }
            location = redirect;
        }
        if (parse_other)
        {
            redirect += "&parseother=yes";
        }
        location = redirect;
    }
    else if (parse_other)
    {
        redirect += "?parseother=yes";
    }
    location = redirect;
    return false;
}

function queueFormParse()
{
    var redirect = window.location.href + "queue/"

    var game = document.getElementById("queue_id").value;
    redirect += game;
    location = redirect;
    return false;
}

function verifierFormParse()
{
    var redirect = window.location.href + "verifier/"

    var game = document.getElementById("verifier_id").value;
    redirect += game;
    location = redirect;
    return false;
}