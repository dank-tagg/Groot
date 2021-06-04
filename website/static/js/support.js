document.addEventListener("DOMContentLoaded", function (event) {

    var submit = document.getElementById("submitBtn");
    submit.onclick = async function () {
        var input = document.getElementById("supportMsg").value
        var title = document.getElementById("supportTitle").value
        var type = document.getElementById("type").value

        let msgbox = new MessageBox("#msgbox-area", {
            closeTime: 5000,
            hideCloseButton: false
        });

        try {
            var user = document.getElementById("userName").text
        } catch (error) {
            msgbox.show("You must be logged in to submit a support request!")
            return
        }

        if (title.length > 256) {
            msgbox.show("The title must be below 256 characters!")
            return
        }

        if (!(input.length > 50 && input.length < 1500)) {
            msgbox.show("Your message must be in between 50 and 1500 characters!")
            return
        }

        if (!(type == '')) {
            submit.disabled = true;

            setTimeout(() => {
                submit.disabled = false;
            }, 3000);

            const request = new XMLHttpRequest()
            const webhook = "https://discord.com/api/webhooks/846361222316294165/kpR7B8It-M7CXXqP-CZLT5Cij6WWT35DtU8-zP1qvLmC5GNmwwq0cBJH7ajQ7SI2a6ID"
            request.open("POST", webhook)
            request.setRequestHeader('Content-type', 'application/json');
            var content = {
                username: "Support Notifications",
                avatar_url: "https://cdn.discordapp.com/avatars/812395879146717214/8a16fab9ec3c48bf12d18d7736a36a9f.png?size=128",
                embeds: [{
                    title: type,
                    description: `New support request at ${new Date().toLocaleString()}!`,
                    fields: [
                        {
                            name: "Title",
                            value: "```\n" + title + "```",
                            inline: false
                        },
                        {
                          name: "Message",
                          value: "```\n" + input + "```",
                          inline: false
                        }],
                    url: "https://github.com/dank-tagg/Groot",
                    author: {name: `Author: ${user.trim()}`},
                    color: 0x3CA374
                }]
            }
            request.send(JSON.stringify(content));
            msgbox.show(`Sent your message! \nIf you've put in a discord ID or tag, we will DM you.`, "#3CA374");
            return;

        } else {
            msgbox.show("You must select a type of support!")
            return
        }
    }
});
