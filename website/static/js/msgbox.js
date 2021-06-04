class MessageBox {
  constructor(id, option) {
    this.id = id;
    this.option = option;
  }
  
  show(msg, color = null, label = "CLOSE", callback = null) {
    if (this.id === null || typeof this.id === "undefined") {
      // if the ID is not set or if the ID is undefined
      throw "Please set the 'ID' of the message box container.";
    }
    
    if (msg === "" || typeof msg === "undefined" || msg === null) {
      // If the 'msg' parameter is not set, throw an error
      
      throw "The 'msg' parameter is empty.";
    }
    
    if (typeof label === "undefined" || label === null) {
      // Of the label is undefined, or if it is null
      label = "CLOSE";
    }
    
    let option = this.option;

    let msgboxArea = document.querySelector(this.id);
    let msgboxBox = document.createElement("DIV");
    let msgboxContent = document.createElement("DIV");
    let msgboxClose = document.createElement("A");
    
    if (msgboxArea === null) {
      // If there is no Message Box container found.
      
      throw "The Message Box container is not found.";
    }

    // Content area of the message box
    msgboxContent.classList.add("msgbox-content");
    msgboxContent.innerText = msg;
    
    msgboxClose.classList.add("msgbox-close");
    msgboxClose.setAttribute("href", "#");
    msgboxClose.innerText = label;
    
    if (color != null) {
        msgboxBox.style.backgroundColor = color
        msgboxBox.style.boxShadow = `0 10px 15px ${color}`
    }

    // Container of the Message Box element
    msgboxBox.classList.add("msgbox-box");
    msgboxBox.appendChild(msgboxContent);

    if (option.hideCloseButton === false
        || typeof option.hideCloseButton === "undefined") {
      // If the hideCloseButton flag is false, or if it is undefined
      
      // Append the close button to the container
      msgboxBox.appendChild(msgboxClose);
    }

    msgboxArea.appendChild(msgboxBox);

    msgboxClose.addEventListener("click", (evt) => {
      evt.preventDefault();
      
      if (msgboxBox.classList.contains("msgbox-box-hide")) {
        // If the message box already have 'msgbox-box-hide' class
        // This is to avoid the appearance of exception if the close
        // button is clicked multiple times or clicked while hiding.
        
        return;
      }

      this.hide(msgboxBox, callback);
    });

    if (option.closeTime > 0) {
      this.msgboxTimeout = setTimeout(() => {
        this.hide(msgboxBox, callback);
      }, option.closeTime);
    }
  }
  
  hide(msgboxBox, callback) {
    if (msgboxBox !== null) {
      // If the Message Box is not yet closed
      msgboxBox.classList.add("msgbox-box-hide");
    }
    
    msgboxBox.addEventListener("transitionend", () => {
      if (msgboxBox !== null) {
        // If the Message Box is not yet closed

        msgboxBox.parentNode.removeChild(msgboxBox);

        clearTimeout(this.msgboxTimeout);
        
        if (callback !== null) {
          // If the callback parameter is not null
          callback();
        }
      }
    });
  }
}