//

function httpGetAsync(theUrl, callback) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            try {
                o = JSON.parse(xmlHttp.responseText);
                callback(o);
            } catch (ex) {
                callback({ "client error": ex, "body": xmlHttp.responseText });
            }
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}

function httpPostAsync(theUrl, o, callback) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            try {
                o = JSON.parse(xmlHttp.responseText);
                callback(o);
            } catch (ex) {
                callback({
                    content: xmlHttp.responseText,
                    "error": ex
                });
            }
    }
    xmlHttp.open("POST", theUrl, true); // true for asynchronous 
    xmlHttp.send(JSON.stringify(o));
}



function removeChild(node) {
    node.parentNode.removeChild(node);
}

function removeChildren(node) {
    while (node.firstChild) {
        node.removeChild(node.firstChild);
    }
}

function dom(tag, attributes) {
    tag = tag.toUpperCase() || 'H1';
    attributes = attributes || [];
    let node = document.createElement(tag);
    for (let key in attributes) {
        node.setAttribute(key, attributes[key]);
    }
    for (let i = 2; i < arguments.length; ++i) {
        let child = arguments[i]; // may be string or other element
        if (typeof child === "string") {
            child = document.createTextNode(child);
            node.textnode = child;
        }
        node.appendChild(child);
    }
    return node;
}


window.onload = function () {
    function postCmd(o) {
        return function () {
            httpPostAsync("/api", o, (res) => {
                console.log(res);
            });
        }
    }
    document.getElementById("start").addEventListener("click", postCmd({ cmd: "start" }));
    document.getElementById("stop").addEventListener("click", postCmd({ cmd: "stop" }));

    let table = document.getElementsByTagName("TABLE")[0];
    function getUpdate() {
        httpGetAsync("/sumo", (res) => {
            removeChildren(table);
            for (key in res) {
                // console.log(key, res[key]);
                keyEle = dom("td", {}, key);
                let v = res[key];
                if (typeof v == "number") {
                    v = v.toFixed(2);
                }
                cntEle = dom("td", { "class": "value" }, "" + v);
                row = dom("tr", {}, keyEle, cntEle);
                table.appendChild(row);
            }
        });
    }
    setInterval(getUpdate, 1000);
}