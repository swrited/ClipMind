(function ($) {
    'use strict';

    // Mobile Menu
    $('.mobile-menu nav').meanmenu({
        meanScreenWidth: "991",
        meanMenuContainer: ".mobile-menu",
        meanMenuClose: "<span class='menu-close'></span>",
        meanMenuOpen: "<span class='menu-bar'></span>",
        meanRevealPosition: "right",
        meanMenuCloseSize: "0",
    });

    // Sticky Header
    $(window).on('scroll', function () {
        var scroll = $(window).scrollTop();
        if (scroll < 245) {
            $("#sticky-header").removeClass("sticky");
            $('.scroll-to-target').removeClass('open');
        } else {
            $("#sticky-header").addClass("sticky");
            $('.scroll-to-target').addClass('open');
        }
    });

    // Scroll to Top
    if ($('.scroll-to-target').length) {
        $(".scroll-to-target").on('click', function () {
            var target = $(this).attr('data-target');
            // animate
            $('html, body').animate({
                scrollTop: $(target).offset().top
            }, 1000);
        });
    }

    // Smooth Scroll
    $('a.nav-scroll[href*="#"]:not([href="#"])').on('click', function () {
        if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
            var target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            if (target.length) {
                $('html, body').animate({
                    scrollTop: target.offset().top
                }, 1000);
                return false;
            }
        }
    });

    // WOW Animation
    new WOW().init();

    // Counter
    $('.counter').counterUp({
        delay: 10,
        time: 1000
    });

    // Carousel
    $('.owl-carousel').owlCarousel({
        loop: true,
        margin: 30,
        nav: true,
        dots: false,
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 2
            },
            1000: {
                items: 3
            }
        }
    });

})(jQuery);
