import React from 'react';

const Footer: React.FC = () => {
    const year = new Date().getFullYear();

    return (
        <footer>
            <a href="mailto:info@intellibots.ca?">info@intellibots.ca</a>
            <p>Copyright © {year} IntelliBots Academy All rights reserved. - Telemetry Systems</p>
        </footer>
    );
};

export default Footer;
