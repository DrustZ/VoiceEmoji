  //language mode, if Chinese, then the processing will be in Chinese language
  //default false for English
  var chinesemode = false;

$(function() {
  var COLORS = [
    '#e21400', '#91580f', '#f8a700', '#f78b00',
    '#58dc00', '#287b00', '#a8f07a', '#4ae8c4',
    '#3b88eb', '#3824aa', '#a700ff', '#d300e7'
  ];

  // Initialize variables
  var $window = $(window);
  var $messages = $('.messages'); // Messages area
  var $inputMessage = $('.inputMessage'); // Input message input box
  chinesemode = ($('#ZH_CN').length > 0)

  // Prompt for setting a username
  var userid='';
  var connected = false;
  var $currentInput = $inputMessage;
  
  /*[Part1] Chat, Websocket related functions*/
  var ws;
  
  //websocket related functions
  //auto connect from https://stackoverflow.com/questions/22431751/websocket-how-to-automatically-reconnect-after-it-dies
  function connect() {
      ws = new WebSocket("wss://10.0.0.182/ws");
      //ws = new WebSocket("wss://voiceemoji.ischool.uw.edu:8080/ws");

      ws.onmessage = function(e){
          var msg =  JSON.parse(e.data)
          if (msg["type"]=='login'){
            connected = true;
            // Display the welcome message
            var message = "Welcome to Voice Emoji Chat – ";
            // log(message, {
            //   prepend: true
            // });
          } else if (msg["type"]=="new message"){
            console.log("testing")
              addChatMessage(msg)
          }
      }

      ws.onclose = function(e) {
        // log('Trying to reconnect...');
        setTimeout(function() {
            connect()
        }, 3000);
      };

      ws.onopen = function(e){
        if (userid == ''){
          userid = Math.random().toString(36).substring(2) + Date.now().toString(36);
          console.log(userid)
        }
        $currentInput = $inputMessage;
        $currentInput.blur();
        ws.send(JSON.stringify({'type':'add user', 'uname':userid}))
      }
      
      ws.onerror = function(err) {
        console.error('Socket encountered error: ', err.message, 'Closing socket');
        ws.close();
      };
  }
//connect to websocket
  connect();    

  // Focus input when clicking on the message input's border
  $inputMessage.click(() => {
    $inputMessage.focus();
  });

  // Sends a chat message
  const sendMessage = () => {
    var message = $inputMessage.val();
    // Prevent markup from being injected into the message
    message = cleanInput(message);
    // if there is a non-empty message and a socket connection
    if (message && connected) {
      $inputMessage.val('');
      addChatMessage({
        username: getLocaleString('You say '),
        message: message
      });
      // tell server to execute 'new message' and send along one parameter
      ws.send(JSON.stringify({'type':'new message', 'message':message}))
    }
  }

  // Log a message
    const log = (message, options) => {
    var $el = $('<li>').addClass('log').text(message);
    addMessageElement($el, options);
  }

  // Adds the visual chat message to the message list
  const addChatMessage = (data, options) => {
    let uname = data.username
    if (uname != getLocaleString('You say ')){
      uname = getLocaleString('The other person says ')
    }
    var $usernameDiv = $('<span class="username"/>')
      .text(uname)
      .css('color', getUsernameColor(uname));
    var $messageBodyDiv = $('<span class="messageBody">')
      .text(data.message);

    var $messageDiv = $('<li class="message"/>')
      .data('username', uname)
      .append($usernameDiv, $messageBodyDiv);

    addMessageElement($messageDiv, options);
  }

  // Adds a message element to the messages and scrolls to the bottom
  // el - The element to add as a message
  // options.fade - If the element should fade-in (default = true)
  // options.prepend - If the element should prepend
  //   all other messages (default = false)
  const addMessageElement = (el, options) => {
    var $el = $(el);

    // Setup default options
    if (!options) {
      options = {};
    }
    if (typeof options.prepend === 'undefined') {
      options.prepend = false;
    }

    // Apply options
    if (options.prepend) {
      $messages.prepend($el);
    } else {
      $messages.append($el);
    }
    $messages[0].scrollTop = $messages[0].scrollHeight;
  }

  // Prevents input from having injected markup
  const cleanInput = (input) => {
    return $('<div/>').text(input).html();
  }

  // Gets the color of a username through our hash function
  const getUsernameColor = (username) => {
    // Compute hash code
    var hash = 7;
    for (var i = 0; i < username.length; i++) {
       hash = username.charCodeAt(i) + (hash << 5) - hash;
    }
    // Calculate color
    var index = Math.abs(hash % COLORS.length);
    return COLORS[index];
  }


/*[Part2] UI interaction related functions*/
  //[Voice] processs input
  var t = null;
  //auto scroll in the message input text area
  $inputMessage.on('input', () => {
    $inputMessage.scrollTop = $inputMessage.scrollHeight;
  });

  // Click copy button
  $(".copybtn").click(function(){
      $inputMessage.select();    
      document.execCommand('copy');
      speakMessage(getLocaleString('text copied'))
  })

  var helpclicks = '0';
  //click help button
  $(".helpbtn").click(function(){
    if (helpclicks == '0') {helpclicks = '';}
    else {helpclicks = '0';}
    speakMessage(helpclicks+getLocaleString('helpMessage'))
  })


  //select an emoji to input it
  $(".emoji").click(function(){
      if ($(this).text().length == 0) {return;}
      changeInputMessageVal($inputMessage.val()+$(this).text())
      speakMessage(getLocaleString("added")+' '+$(this).text())
  })
    
  //navigate through emojis
  $(".prevbtn").click(function(){
      let startidx = $('.emoji').data("startIdx");
      if (startidx >= 5){
        $('.emoji').data('startIdx', startidx-5);
        $('.emoji').data('endIdx', startidx);
        showEmojisFromDesc(currentemojis);
      }
  })

  $('.nextbtn').click(function(){
    let startidx = $('.emoji').data("startIdx");
    let elenth = currentemojis.length
    if (startidx+5 < elenth){
      $('.emoji').data('startIdx', startidx+5);
      $('.emoji').data('endIdx', Math.min(startidx+10, elenth));
      showEmojisFromDesc(currentemojis);
    }
  })

  //send the message
  $(".sendbtn").click(function(){
      speakMessage($inputMessage.val())
      showEmojisFromDesc(null)
      if (userid){
        sendMessage();
      }
  })

  //trigger speech function
  $('.speechbtn').click(function(e){
    //clear ding sound
    audio.src = '';
    audio.play();
      var $btn = $('.speechbtn')
      e.preventDefault()
      var $btn2 = $('.copybtn')
      if ($btn2.data('recording')){
          //record stop, process
          $btn2.removeData('recording')
          // $btn.addClass("loading")
          $btn2.data('processing', true)
          $btn.attr('aria-busy',true)
          //wait
          stopRecording();
      } else if ($btn2.data('processing')){
      } else {
          //start recording
          startRecording().then(function(){
              $btn.focus();
          }, function(error){
              console.log(error)
          })
      }
      //get the focus back because safari will
      //misteriously lose focus sometimes.
      $btn.focus()
  })
  
});

$.ajaxPrefilter( function (options) {
  if (options.crossDomain && jQuery.support.cors) {
    var http = (window.location.protocol === 'http:' ? 'http:' : 'https:');
    //we need to make CORS call, hence we need a proxy server
    //if this weburl is not working , try the next line
    //or other proxies like https://corsproxy.github.io/, https://nordicapis.com/10-free-to-use-cors-proxies/
    //related: https://stackoverflow.com/questions/47076743/cors-anywhere-herokuapp-com-not-working-503-what-else-can-i-try
    options.url = http + '//cors-anywhere.herokuapp.com/' + options.url;
    //options.url = "http://cors.corsproxy.io/url=" + options.url;
  }
});

/*[Part3] Speech recording related functions*/
{
  URL = window.URL || window.webkitURL;
  var gumStream = null;
  //stream from getUserMedia() 
  var rec;
  //Recorder.js object 
  var input;
  //MediaStreamAudioSourceNode we'll be recording 
  // shim for AudioContext when it's not avb. 
  var AudioContext = window.AudioContext || window.webkitAudioContext;
  var audioContext = null

  function startRecording(){
      var constraints = {
          audio: true,
          video: false
      } 
      if (audioContext == null){
        audioContext = new AudioContext();
      }
      return new Promise(function(resolve, reject) {
          navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
                //console.log("getUserMedia() success, stream created, initializing Recorder.js ..."); 
                /* assign to gumStream for later use */
                gumStream = stream;
                /* use the stream */
                input = audioContext.createMediaStreamSource(stream);
                /* Create the Recorder object and configure to record mono sound (1 channel) Recording 2 channels will double the file size */
                rec = new Recorder(input, {
                    numChannels: 1
                })
                $('.copybtn').data('recording', true)
                //start the recording process 
                rec.record()
                $('.sr-only').html(getLocaleString('Please start speaking'))
                audio.src = 'ding.mp3';
                audio.play();
                console.log("Recording started");
                resolve()
            }).catch(function(err) {
                reject(err)
            });
        
      });
      
  }

  function stopRecording() {
      console.log("stopButton clicked");
      //tell the recorder to stop the recording 
      rec.stop(); 
      //stop microphone access 
      gumStream.getAudioTracks()[0].stop();
      //create the wav blob and pass it on to createDownloadLink 
      rec.exportWAV(createDownloadLink);
  }

  function createDownloadLink(blob) {
      var refreshIntervalId = setInterval(function(){ 
        if ($('.sr-only').html() == getLocaleString('processing')){
          $('.sr-only').html('')
        } else {
          speakMessage(getLocaleString('processing'))
        }
       }, 1800);

      var url = URL.createObjectURL(blob);
        var reader = new FileReader();
        reader.readAsDataURL(blob); 
        reader.onloadend = function() {
            var base64data =  reader.result.split(',')[1];                
            fetch('/messages', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                  message: base64data,
                  language: chinesemode ? 'zh-CN' : 'en-US',
                  premessage: $('.inputMessage').val()})
                }).then(res => {
                      clearInterval(refreshIntervalId);
                      var $btn = $('.speechbtn')
                      $btn.focus()
                      $btn.attr('aria-busy',false)
                      $('.copybtn').removeData('processing')
                      // $btn.removeClass('red loading')
                      $btn.addClass('green')
                      $btn.html(getLocaleString('Speech'))
                      if (res.status === 201) {
                          res.json().then(resj => {
                              processResponse(resj)
                          })
                      }
                  });
          } 
  }
}


let audio = new Audio();

//process voice recognition response
function processResponse(resj){
  console.log(resj)
  var content = $('.inputMessage').val()
  //check emoji selection first
  if (resj.hasOwnProperty('selection') && 
      $('.emoji').eq(resj.selection).html().length > 0){
      var selected_emoji = $('.emoji').eq(resj.selection).html()
      changeInputMessageVal(content+selected_emoji)
      //command feedback
      speakMessage(getLocaleString("added")+' '+selected_emoji)
      return;
  }
  
  //check any emoji commands 
  if ((resj.hasOwnProperty('delete') ||
      resj.hasOwnProperty('change')) && 
      (match = emojiReg.exec(content)) != null){
      //seek for last emoji index
      let lastidx = match.index
      let lastlen = match[0].length
      while ((match = emojiReg.exec(content)) != null)
      { 
        lastidx = match.index 
        lastlen = match[0].length
      }
      
      if (resj.hasOwnProperty('delete')) {
          changeInputMessageVal(content.substring(0, lastidx)
                                + content.substring(lastidx+lastlen))
          speakMessage(getLocaleString('emoji removed'))
      } else {
        if (resj.change.length > 0){
          changeInputMessageVal(content.substring(0, lastidx)
                                + resj.change+content.substring(lastidx+lastlen))
          speakMessage(
            getLocaleString("emoji changed to")+' '+resj.change)
        } else {
          speakMessage(getLocaleString("could not find emoji")+' '+resj.query);
        }
      }
      return;
  }
  

  //show suggested emojis
  if (resj.hasOwnProperty('show')){
    let emojis = []
    if ($('.emoji').eq(0).html().length == 0){ 
      speakMessage(getLocaleString('no emoji suggestions'))
    } else {
      for (let i = 0; i < 5; ++i){
        let emj = $('.emoji').eq(i).html()
        if (emj.length == 0) 
          { break } 
        emojis.push($('.emoji').eq(i).html())
      }
      let speakres = formatEmojiSuggestions(
        getLocaleString("Suggested emojis are"), emojis)
      speakMessage(speakres)
    }
    return;
  }

  //update emojis
  if (resj.hasOwnProperty('emojis')){
      $('.prevbtn').attr('display', 'none');
      //add ding sound for indicating emojis
      audio.src = 'ding.mp3';
      audio.play();
      //set the start/end index of the emojis
      $('.emoji').data("startIdx", 0);
      $('.emoji').data("endIdx", 5);
      showEmojisFromDesc(resj.emojis)
      //show returned emoji results for emoji quests
      if (resj.text.trim().length == 0){
        if (resj.emojis.length == 0){
          $('.nextbtn').css('display', 'none');
          speakMessage(getLocaleString("no emoji found"))
        } else {
          let speakres = formatEmojiSuggestions(
            getLocaleString("Possible emojis are"), resj.emojis)
          speakMessage(speakres)
        }
      }
  } else {
      showEmojisFromDesc(null)
  }

  if (resj.text.trim().length > 0){
      changeInputMessageVal(content+' '+resj.text.trim())
      speakMessage(resj.text.trim()+' '+getLocaleString('emoji suggestions available'));
  }
}

function formatEmojiSuggestions(prefix, emojis){
  let speakres = prefix
  for (let i in emojis){
    let ordstr = ' '+getLocaleString('first')+' '
    if (i == 1) {ordstr = ' '+getLocaleString('second')+' '}
    if (i == 2) {ordstr = ' '+getLocaleString('third')+' '}
    if (i == 3) {ordstr = ' '+getLocaleString('fourth')+' '}
    if (i == 4) {ordstr = ' '+getLocaleString('fifth')+' '}
    speakres += ordstr + emojis[i]
    if (i == 4) {break;}
  }
  if (emojis.length > 5){
    speakres += getLocaleString('more available');
  }
  return speakres
}

/*[Part4] Emoji recording related functions*/
{
  //function for processing voice input
  var emojiReg = /(?:[\u2700-\u27bf]|(?:\ud83c[\udde6-\uddff]){2}|[\ud800-\udbff][\udc00-\udfff])[\ufe0e\ufe0f]?(?:[\u0300-\u036f\ufe20-\ufe23\u20d0-\u20f0]|\ud83c[\udffb-\udfff])?(?:\u200d(?:[^\ud800-\udfff]|(?:\ud83c[\udde6-\uddff]){2}|[\ud800-\udbff][\udc00-\udfff])[\ufe0e\ufe0f]?(?:[\u0300-\u036f\ufe20-\ufe23\u20d0-\u20f0]|\ud83c[\udffb-\udfff])?)*/g
  var need_num = 5 //needed emojis to show

  //change input message val programmatically without 
  //invoking its triggers
  function changeInputMessageVal(content){
      $('.inputMessage').data("processing", true)
      $('.inputMessage').val(content)
      $('.inputMessage').removeData("processing")
  }

//raw input text change processors / deprecated
  {
  function seletNthEmoji(text, n){
      var content = $('.inputMessage').val()
      var lowert = content.toLowerCase().trim()
      if (lowert.endsWith(text)){
          //check emoji selection first
          changeInputMessageVal(content.substring(0, content.toLowerCase().lastIndexOf(text))
                                +$('.emoji').eq(n).html())
          return true;
      } 
      return false
  }

  }

  var currentemojis = null
  function showEmojisFromDesc(emojis){
      currentemojis = emojis
      for (var i = 0; i < 5; ++i){
          $('.emoji').eq(i).html('')
          $(".emoji").css('visibility', 'hidden');
          //remove aria accessibility desc
          $('.emoji').eq(i).removeAttr('role')
          $('.emoji').eq(i).removeAttr('tabindex')
      }
      
      if (emojis == null) { 
        $('.nextbtn').css('display', 'none');
        $('.prevbtn').css('display', 'none');  
        return; 
      }

      let startidx = $('.emoji').data("startIdx")
      let endidx = $('.emoji').data('endIdx')
      console.log("start end"+startidx + ' '+endidx)
      if (emojis.length > 5){
        console.log("emoji length" + emojis.length)
        $('.nextbtn').css('display', 'block');
        $('.prevbtn').css('display', 'block');

        if (startidx == 0){
          $('.prevbtn').css('display', 'none');  
        } else if (emojis.length <= endidx){
          $('.nextbtn').css('display', 'none');
        }

      } else {
        $('.nextbtn').css('display', 'none');
        $('.prevbtn').css('display', 'none');
      }

      for (var j = startidx; j < endidx; ++j){
          let i = j-startidx;
          $('.emoji').eq(i).html(emojis[j])
          //add aria accessibility desc
          $(".emoji").css('visibility', 'visible');
          $('.emoji').eq(i).attr('role', 'button')
          $('.emoji').eq(i).attr('tabindex', '0')
          $('.emoji').eq(i).attr('aria-label',
                getLocaleString('emoji')+' '+emojis[j])
      }
  }
}

//translate command to output text
function getLocaleString(command){
  switch (command) {
    case 'emoji':
      return chinesemode ? '表情' : 'emoji';
    case 'added':
      return chinesemode ? '已插入' : 'added';
    case 'first':
      return chinesemode ? '第一个' : 'first';
    case 'second':
      return chinesemode ? '第二个' : 'second';
    case 'third':
      return chinesemode ? '第三个' : 'third';
    case 'fourth':
      return chinesemode ? '第四个' : 'fourth';
    case 'fifth':
      return chinesemode ? '第五个' : 'fifth';
    case 'emoji removed':
      return chinesemode ? '表情已删除' : 'emoji removed';
    case 'emoji changed to':
      return chinesemode ? '表情已变为' : 'emoji changed to';
    case 'could not find emoji':
      return chinesemode ? '找不到相关表情' : 'could not find emoji';
    case 'no emoji suggestions':
      return chinesemode ? '无建议表情' : 'no emoji suggestions';
    case 'Suggested emojis are':
      return chinesemode ? '建议的表情有' : 'Suggested emojis are';
    case 'no emoji found':
      return chinesemode ? '没有找到表情' : 'no emoji found';
    case 'Possible emojis are':
      return chinesemode ? '找到这些表情' : 'Possible emojis are'; 
    case 'tap to insert':
      return chinesemode ? '点击插入' : 'tap to insert';
    case 'You say ':
      return chinesemode ? '你说 ' : 'You say ';
    case 'The other person says ':
      return chinesemode ? '对方说 ' : 'The other person says ';
    case 'Please start speaking':
      return chinesemode ? '请说话' : 'Please start speaking';
    case 'Speech':
        return chinesemode ? '说话' : 'Speech';
    case 'emoji suggestions available':
      return chinesemode ? '有建议表情' : 'emoji suggestions available';
    case 'text copied':
      return chinesemode ? '文本已复制' : 'text copied';
    case 'processing':
      return chinesemode ? '处理中' : 'processing';
    case 'helpMessage':
      return chinesemode ? '1. 您可以用 给我表情 句式来查询表情，例如 给我一百分的表情。 2. 在说话中用一个词加上表情关键词来直接替换为表情， 例如 春天来了花朵表情。 3. 想看当前可用的表情，可以说有什么表情。 4. 如果要把键入的表情换成其他表情，可以说把表情改成，例如把表情改成气球表情。5. 如果要删除键入的表情，可以说删除表情。\
      6.可以点击按钮来键入表情，也可以说第几个表情，比如第三个表情。7.如果说话里没有表情关键字，则会根据说话的内容返回相关表情。' 
      : '1. you can say emoji search plus description plus emoji to search an emoji. For example, emoji search angry face emoji. 2. you can add the emoji keyword after a noun word to replace it into an emoji. For example, today is cold freezing emoji. 3. you can say read emojis to hear suggested emoji options. \
      4. you can say change the emoji to description to change the last entered emoji into other emoji. for example, change the emoji to balloon emoji. You can also use skin or color keyword to change the skin or color of the emoji. For example, change the meoji to black skin, or change the emoji to black color.\
      5. you can say delete emoji to remove the last entered emoji. 6. you can say the first emoji to input emojis, or click the emoji to input emoji. 7. if there is no emoji keyword in your speech, the system will suggest emoji based on the contents of your speech.'
    case 'more available':
      return chinesemode ? '更多表情可用' : 'more available';
  }
}

//speech synthesis functions
{
  var synth = window.speechSynthesis;
  var voices = [];
  var voiceIdx = -1;
  var voiceCHNIdx = -1;

  function chooseVoiceList() {
    voices = synth.getVoices().sort(function (a, b) {
        const aname = a.name.toUpperCase(), bname = b.name.toUpperCase();
        if ( aname < bname ) return -1;
        else if ( aname == bname ) return 0;
        else return +1;
    });
    for(i = 0; i < voices.length ; i++) {

      if (voices[i].lang.toLowerCase() == 'en-us' && voiceIdx == -1){
          voiceIdx = i;
      }
      if (voices[i].lang.toLowerCase() == 'zh-cn' && voiceCHNIdx == -1){
        voiceCHNIdx= i;
      }
    }
  }

  chooseVoiceList();
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = chooseVoiceList;
  }

  function speakMessage(text){ 
      if (text.length == 0) return
      
      //make text into segments of pure text and emojis
      var textSegments = []
      var lastSegIndex = 0
      while ((match = emojiReg.exec(text)) != null) {
          textSegments.push(text.substring(lastSegIndex, match.index));
          textSegments.push(getLocaleString("emoji")+" "+match[0]);
          lastSegIndex = match.index+match[0].length
      }
      if (lastSegIndex < text.length){
          textSegments.push(text.substring(lastSegIndex))
      }
      
      //for screen reader
      sr_only = $('.sr-only')
      $('.sr-only').html(textSegments.join(' '));
      console.log($('.sr-only').html())

      if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        synth.cancel();
      }
  }

  function speakSegments(ssu, segments, index) {
      if(index >= segments.length)
          return;

      var sentence = segments[index];
      ssu.text = sentence;
      ssu.onend = function() {
          speakSegments(ssu, segments, ++index);
      };
      synth.speak(ssu);
  }
}


