$(document).ready(function() {
    const signalOutputData = document.querySelector('#signalOutputData')
    const signalOutputLoading = document.querySelector('#signalOutputLoading')
    if(signalOutputData){
        setTimeout(() => {
            signalOutputLoading.classList.add('d-none')
            signalOutputData.classList.remove('d-none')
        }, 2000);
    }
    const serverErrorAlert = document.querySelector('#serverErrorAlert')
    if(serverErrorAlert){
        setTimeout(()=> {
            serverErrorAlert.classList.add('d-none')
        },5000)
    }
    if ( window.history.replaceState ) {
        window.history.replaceState( null, null, window.location.href );
    }

    const bourseBtnGroup = document.querySelectorAll('#bourseBtnGroup > button')
    const bourseUploadFile = document.querySelector('#bourseUploadFile')
    const bourseSearch = document.querySelector('#bourseSearch')

    bourseBtnGroup.forEach(btn => {
        btn.addEventListener('click', (e) => {
            switch(e.target.innerHTML){
                case 'آپلود فایل':
                        bourseSearch.classList.add('d-none')
                        bourseUploadFile.classList.remove('d-none')
                    break
                case 'جست و جو':
                    bourseUploadFile.classList.add('d-none')
                    bourseSearch.classList.remove('d-none')
                    break
            }
        })
    })
    const csrftoken = $('input[name=csrfmiddlewaretoken]').val()
    $('#tickerInput').on('input', function(e){
        const value = e.target.value
        if(value.length >= 2){
            $.ajax({
                url: '/backtest/bourse/tickers/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                data: {
                    tickerInput: e.target.value,
                },
                success: function(data, status){
                    if (data){
                        $('#tickersResult').removeClass('d-none')
                        $('#tickersResult').html(() => {
                            $(this).removeClass('d-none')
                            let resultsHtml = data.map(d => `<a href="#" class="list-group-item list-group-item-action" ticker-id="${data.indexOf(d) + 1}">${d}</li>`)
                            resultsHtml = '<div class= "list-group">' + resultsHtml.join('') + '</div>'
                            return resultsHtml
                        })
                        $('a[ticker-id]').each(function(i,elem){
                            $(this).click(function(e){
                                $('#tickerInput').val(e.target.innerHTML)
                                $('#tickersResult').addClass('d-none')
                                $('#tickersResult').html('')
                            })
                        })
                    }
                }
            })
        } else {
            $('#tickersResult').addClass('d-none')
            $('#tickersResult').html('')
        }
    })
    $("#tickerStartDate").persianDatepicker({
        initialValue: false,
        observer: true,
        format: 'YYYY/MM/DD',
        navigator: {
            text: {
              btnNextText: '←',
              btnPrevText: '→'
            }
        }
    })
    $("#tickerEndDate").persianDatepicker({
        initialValue: false,
        observer: true,
        format: 'YYYY/MM/DD',
        navigator: {
            text: {
              btnNextText: '←',
              btnPrevText: '→'
            }
        }
    })

    if (window.matchMedia('(max-width: 768px)').matches){
        $("#bourseSearchForm").addClass('flex-column')
    } else {
        $("#bourseSearchForm").remove('flex-column')
    }
    
})
