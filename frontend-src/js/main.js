
(function ($) {
    "use strict";


    /*==================================================================
    [ Validate ]*/
    var input = $('.validate-input .input100');

    function validateForm(){
        var check = true;

        for(var i=0; i<input.length; i++) {
            if(validate(input[i]) == false){
                showValidate(input[i]);
                check=false;
            }
        }

        return check;
    }

    $('.validate-form').on('submit', validateForm);

    $('.validate-form .input100').each(function(){
        $(this).focus(function(){
           hideValidate(this);
        });
    });

    function validate (input) {
        if($(input).attr('type') == 'email' || $(input).attr('name') == 'email') {
            if($(input).val().trim().match(/^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{1,5}|[0-9]{1,3})(\]?)$/) == null) {
                return false;
            }
        }
        else {
            if($(input).val().trim() == ''){
                return false;
            }
        }
    }

    function showValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function hideValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).removeClass('alert-validate');
    }

    $("#loginform").on("submit", (e) => {
        e.preventDefault();
        if (validateForm() === false) {
            return;
        }

        $("#loginview").addClass("hiddenitem");
        $("#loadingview").removeClass("hiddenitem");

        const urlParams = new URLSearchParams(window.location.search);
        const realm = urlParams.get("realm") === null ? "default" : urlParams.get("realm");

        $.ajax({
            type: "POST",
            url: `/api/auth/login/${realm}`,
            data: JSON.stringify({
                "username": $("#usernameinput").val(),
                "password": $("#passwordinput").val()
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: (data) => {
                window.location.replace(data.redirect);
                $("#loadingview").addClass("hiddenitem");
                $("#loginview").removeClass("hiddenitem");
            },
            error: (data) => {
                console.log(data);
                if ("responseJSON" in data) {
                    $("#errortext").text(data.responseJSON.message);
                } else {
                    $("#errortext").text(data.statusText);
                }
                $("#errorbox").removeClass("hiddenitem");
                $("#loadingview").addClass("hiddenitem");
                $("#loginview").removeClass("hiddenitem");
            }
        });
    });

})(jQuery);
