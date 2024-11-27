document.addEventListener('DOMContentLoaded', () => {
    send_query();
});

function send_query() {
    setInitialNumUvlFilterMaxMin()
    setInitialDatesMaxMin()
    setInitialNumConfigurationsFilterMaxMin()

    console.log("send query...")

    document.getElementById('results').innerHTML = '';
    document.getElementById("results_not_found").style.display = "none";
    console.log("hide not found icon");

    const filters = document.querySelectorAll('#filters input, #filters select, #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {
            const csrfToken = document.getElementById('csrf_token').value;

            const startDate = document.querySelector('#start_date');
            const endDate = document.querySelector('#end_date');
            
            setDatesMaxMin(filter, startDate, endDate);

            const minUvl = document.querySelector('#min_uvl');
            const maxUvl = document.querySelector('#max_uvl');
            
            setNumFilterMaxMin(filter, minUvl, maxUvl);

            const minNumConfg = document.querySelector('#min_num_configurations');
            const maxNumConfg = document.querySelector('#max_num_configurations');
            
            setNumFilterMaxMin(filter, minNumConfg, maxNumConfg);

            const searchCriteria = {
                csrf_token: csrfToken,
                query: document.querySelector('#query').value,
                publication_type: document.querySelector('#publication_type').value,
                start_date: startDate.value,
                end_date: endDate.value,
                min_uvl: minUvl.value,
                max_uvl: maxUvl.value,
                by_valid_uvls: document.querySelector('#by_valid_uvls').value,
                min_num_configurations: minNumConfg.value,
                max_num_configurations: maxNumConfg.value,
                sorting: document.querySelector('[name="sorting"]:checked').value,
            };

            console.log(document.querySelector('#publication_type').value);

            fetch('/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchCriteria),
            })
                .then(response => response.json())
                .then(data => {

                    console.log(data);
                    document.getElementById('results').innerHTML = '';

                    // results counter
                    const resultCount = data.length;
                    const resultText = resultCount === 1 ? 'dataset' : 'datasets';
                    document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

                    if (resultCount === 0) {
                        console.log("show not found icon");
                        document.getElementById("results_not_found").style.display = "block";
                    } else {
                        document.getElementById("results_not_found").style.display = "none";
                    }


                    data.forEach(dataset => {
                        let card = document.createElement('div');
                        card.className = 'col-12';
                        card.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex align-items-center justify-content-between">
                                        <h3><a href="${dataset.url}">${dataset.title}</a></h3>
                                        <div>
                                            <span class="badge bg-primary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
                                        </div>
                                    </div>
                                    <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Description
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            <p class="card-text">${dataset.description}</p>
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Authors
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.authors.map(author => `
                                                <p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>
                                            `).join('')}
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Tags
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('')}
                                        </div>

                                    </div>
                                                <div class="row mb-2">
                                        <div class="col-md-4 col-12">
                                            <span class="text-secondary">Rating</span>
                                        </div>
                                        <div class="col-md-8 col-12 d-flex align-items-center">
                                            <div id="star-rating-${dataset.id}" class="stars" style="color: gold;">
                                                ${'<span data-value="1">★</span>'.repeat(5)} <!-- Estrellas para interacción -->
                                            </div>
                                                <span id="average-rating-${dataset.id}" class="ms-2">-</span> <!-- Valor inicial vacío -->
                                        </div>
                                    </div>

                                    <div class="row">

                                        <div class="col-md-4 col-12">

                                        </div>
                                        <div class="col-md-8 col-12">
                                            <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                View dataset
                                            </a>
                                            <a href="/dataset/download/${dataset.id}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                Download (${dataset.total_size_in_human_format})
                                            </a>
                                        </div>


                                    </div>

                                </div>
                            </div>
                        `;

                        document.getElementById('results').appendChild(card);
                    });
                });
                updateAverageRating(dataset.id)
        });
    });
}

function setInitialDatesMaxMin() {
    const startDateInput = document.querySelector('#start_date');
    const endDateInput = document.querySelector('#end_date');
    const today = new Date();

    const startDate = new Date(startDateInput.value);
    if (!isNaN(startDate)) {
        const date = today > startDate ? startDate : today
        endDateInput.min = dateToString(date);
    } else {
        endDateInput.min = ""
    }

    const endDate = new Date(endDateInput.value);
    if (!isNaN(endDate)) {
        const date = today > endDate ? endDate : today
        startDateInput.max = dateToString(date);    
    } else {
        startDateInput.max = dateToString(today);
    }
}

function setDatesMaxMin(filter, startDateInput, endDateInput) {
    if (filter.id === startDateInput.id) {
        const startDate = new Date(startDateInput.value);
        if (isNaN(startDate)) {
            endDateInput.min = "";
        } else {
            endDateInput.min = dateToString(startDate);
        }
    } else if (filter.id === endDateInput.id) {
        const endDate = new Date(endDateInput.value);
        const today = new Date();
        if (isNaN(endDate)) {
            startDateInput.max = dateToString(today);
        } else {
            const date = today > endDate ? endDate : today
            startDateInput.max = dateToString(date);
        }
    }
}

function dateToString(date) {
    return date.getFullYear() + "-" + (date.getMonth() + 1) + "-" + date.getDate()
}

function setInitialNumUvlFilterMaxMin() {
    const minUvl = document.querySelector('#min_uvl');
    const maxUvl = document.querySelector('#max_uvl');

    const numMin = parseInt(minUvl.value);
    if (!isNaN(numMin)) {
        maxUvl.min = numMin
    }

    const numMax = parseInt(maxUvl.value);
    if (!isNaN(numMax)) {
        minUvl.max = numMax
    }
}

function setInitialNumConfigurationsFilterMaxMin() {
    const minConf = document.querySelector('#min_num_configurations');
    const maxConf = document.querySelector('#max_num_configurations');

    const numMin = parseInt(minConf.value);
    if (!isNaN(numMin)) {
        maxConf.min = numMin
    }

    const numMax = parseInt(maxConf.value);
    if (!isNaN(numMax)) {
        minConf.max = numMax
    }
}

function setNumFilterMaxMin(filter, min, max) {
    if (filter.id === min.id) {
        const num = parseInt(min.value);
        if (isNaN(num)) {
            max.min = 0;
        } else {
            max.min = num;
        }
    } else if (filter.id === max.id) {
        const num = parseInt(max.value);
        if (isNaN(num)) {
            min.max = "";
        } else {
            min.max = num;
        }
    } 
}

function formatDate(dateString) {
    const options = {day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: 'numeric'};
    const date = new Date(dateString);
    return date.toLocaleString('en-US', options);
}

function set_tag_as_query(tagName) {
    const queryInput = document.getElementById('query');
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_publication_type_as_query(publicationType) {
    const publicationTypeSelect = document.getElementById('publication_type');
    for (let i = 0; i < publicationTypeSelect.options.length; i++) {
        if (publicationTypeSelect.options[i].text === publicationType.trim()) {
            // Set the value of the select to the value of the matching option
            publicationTypeSelect.value = publicationTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {

    // Reset the search query
    let queryInput = document.querySelector('#query');
    queryInput.value = "";
    // queryInput.dispatchEvent(new Event('input', {bubbles: true}));

    // Reset the publication type to its default value
    let publicationTypeSelect = document.querySelector('#publication_type');
    publicationTypeSelect.value = "any"; // replace "any" with whatever your default value is
    // publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));

    let validUvlCheckbox = document.querySelector('#by_valid_uvls');
    validUvlCheckbox.checked = false; 

    // Reset the dates to none
    let startDateInput = document.querySelector('#start_date');
    startDateInput.value = "";

    let endDateInput = document.querySelector('#end_date');
    endDateInput.value = "";
    
    // Reset the number of uvl models filters
    let minUvlInput = document.querySelector('#min_uvl');
    minUvlInput.value = "";

    let maxUvlInput = document.querySelector('#max_uvl');
    maxUvlInput.value = "";
    
    // Reset the number of configurations filters
    let maxConfigurationsInput = document.querySelector('#max_num_configurations');
    maxConfigurationsInput.value = "";

    let minConfigurationsInput = document.querySelector('#min_num_configurations');
    minConfigurationsInput.value = "";

    // Reset the sorting option
    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value == "newest"; // replace "default" with whatever your default value is
        // option.dispatchEvent(new Event('input', {bubbles: true}));
    });

    // Perform a new search with the reset filters
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));

    setInitialNumUvlFilterMaxMin()
    setInitialDatesMaxMin()
}

document.addEventListener('DOMContentLoaded', () => {

    //let queryInput = document.querySelector('#query');
    //queryInput.dispatchEvent(new Event('input', {bubbles: true}));

    let urlParams = new URLSearchParams(window.location.search);
    let queryParam = urlParams.get('query');

    if (queryParam && queryParam.trim() !== '') {

        const queryInput = document.getElementById('query');
        queryInput.value = queryParam
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
        console.log("throw event");

    } else {
        const queryInput = document.getElementById('query');
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
    }
});


function updateAverageRating(datasetId) {
    fetch(`/datasets/${datasetId}/average-rating`)
        .then(response => response.json())
        .then(data => {
            const ratingValue = data.average_rating.toFixed(1);
            document.getElementById('average-rating-' + datasetId).innerText = ratingValue;

            // Resaltar el número correcto de estrellas en amarillo
            const starContainer = document.getElementById('star-rating-' + datasetId);
            highlightStars(starContainer, Math.round(data.average_rating));
        })
        .catch(error => console.error('Error fetching average rating:', error));
}

function highlightStars(container, rating) {
    container.querySelectorAll('span').forEach(star => {
        const starValue = star.getAttribute('data-value');
        star.style.color = starValue <= rating ? '#FFD700' : '#ddd'; // Estrellas doradas según el rating
    });
}